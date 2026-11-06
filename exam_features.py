import streamlit as st
import streamlit.components.v1 as components
import html
import json


def highlight_vignette(vignette, question_id):
    """Display vignette with automatic yellow highlighting."""
    import html
    import json
    import streamlit.components.v1 as components

    safe_text = html.escape(str(vignette))
    text_json = json.dumps(safe_text)
    key_json = json.dumps("eoc_highlight_" + str(question_id))

    page = """
    <div id="vignette" style="
        font-family: Arial, sans-serif;
        font-size: 17px;
        line-height: 1.7;
        padding: 12px;
        white-space: pre-wrap;
        color: #222;
    "></div>
    <button id="clear">Clear Highlights</button>
    <script>
    const text = __TEXT__;
    const key = __KEY__;
    const box = document.getElementById("vignette");

    box.innerHTML = localStorage.getItem(key) || text;

    box.addEventListener("mouseup", () => {
        const selection = window.getSelection();
        if (!selection.rangeCount || selection.isCollapsed) return;
        const range = selection.getRangeAt(0);
        if (!box.contains(range.commonAncestorContainer)) return;

        const mark = document.createElement("mark");
        mark.style.backgroundColor = "#fff176";
        try {
            range.surroundContents(mark);
            localStorage.setItem(key, box.innerHTML);
            selection.removeAllRanges();
        } catch (e) {}
    });

    document.getElementById("clear").onclick = () => {
        box.innerHTML = text;
        localStorage.removeItem(key);
    };
    </script>
    """

    page = page.replace("__TEXT__", json.dumps(text_json))
    page = page.replace("__KEY__", key_json)

    components.html(page, height=450, scrolling=False)


def download_progress():
    """Let users download their current practice session."""
    import json

    fields = [
        "mode",
        "question_index",
        "answered",
        "selected_answer",
        "score",
        "answered_count",
        "withheld_count",
    ]

    progress = {
        "version": 1,
        "app": "yesenia-eoc-practice",
        "question_count": len(st.session_state.targets),
        "questions": [
            json.loads(json.dumps(item, default=lambda obj: vars(obj)))
            for item in st.session_state.targets
        ],
        "session": {
            field: st.session_state.get(field)
            for field in fields
        },
    }

    st.download_button(
        "Save My Progress",
        data=json.dumps(progress, indent=2),
        file_name="yesenia_eoc_progress.json",
        mime="application/json",
        use_container_width=True,
    )


def resume_progress():
    """Restore a previously saved practice session."""
    from types import SimpleNamespace

    uploaded = st.file_uploader(
        "Resume Previous Session",
        type=["json"],
        key="resume_progress_upload",
    )

    if uploaded is None:
        return

    if st.button("Restore My Progress"):
        try:
            data = json.load(uploaded)

            if data.get("version") != 1:
                raise ValueError("Unsupported save file version.")

            if data.get("app") != "yesenia-eoc-practice":
                raise ValueError("This file belongs to another app.")

            questions = data.get("questions", [])
            session = data.get("session", {})

            if not questions or len(questions) > 1000:
                raise ValueError("Invalid question count.")

            required = {
                "vignette", "lead_in", "answer_choices",
                "correct_answer", "rationale", "teaching_point"
            }

            if not all(isinstance(q, dict) and required <= q.keys()
                       for q in questions):
                raise ValueError("Invalid question data.")

            index = session.get("question_index", 0)
            if type(index) is not int or not 0 <= index <= len(questions):
                raise ValueError("Invalid question position.")

            def convert(obj):
                if isinstance(obj, dict):
                    return SimpleNamespace(
                        **{k: convert(v) for k, v in obj.items()}
                    )
                if isinstance(obj, list):
                    return [convert(v) for v in obj]
                return obj

            restored = [convert(q) for q in questions]

            for field in ("score", "answered_count", "withheld_count"):
                value = session.get(field, 0)
                if type(value) is not int or not 0 <= value <= len(questions):
                    raise ValueError(f"Invalid {field}.")

            if session.get("mode") not in ("Yesenia Practice",):
                raise ValueError("Invalid practice mode.")

            if type(session.get("answered")) is not bool:
                raise ValueError("Invalid answer status.")

            selected = session.get("selected_answer")
            if selected is not None and selected not in ("A", "B", "C", "D", "E"):
                raise ValueError("Invalid selected answer.")

            st.session_state.targets = restored
            for field in (
                "mode", "question_index", "answered",
                "selected_answer", "score", "answered_count",
                "withheld_count"
            ):
                st.session_state[field] = session[field]

            st.session_state.current_item = None
            st.success("Progress restored successfully.")
            st.rerun()

        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as e:
            st.error(f"Unable to restore progress: {e}")
