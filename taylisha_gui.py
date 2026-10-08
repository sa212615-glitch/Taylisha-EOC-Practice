import random
import streamlit as st

from agents.item_generator import load_targets, generate_item
from question_bank import load_question_bank
from agents.item_quality import approve_item
from app import save_json, select_eoc_context, OUTPUT_DIR


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="PA EOC Practice",
    page_icon="🩺",
    layout="wide",
)

st.title("PA EOC Practice")
st.caption(
    "AI-generated and clinically reviewed Physician Assistant practice questions"
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "mode": None,
    "targets": [],
    "question_index": 0,
    "current_item": None,
    "answered": False,
    "selected_answer": None,
    "score": 0,
    "answered_count": 0,
    "withheld_count": 0,
    "generating": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# START PRACTICE SESSION
# ============================================================

def start_session(database, mode_name):
    targets = load_question_bank()
    targets = targets.copy()
    random.shuffle(targets)

    st.session_state.mode = mode_name
    st.session_state.targets = targets
    st.session_state.question_index = 0
    st.session_state.current_item = None
    st.session_state.answered = False
    st.session_state.selected_answer = None
    st.session_state.score = 0
    st.session_state.answered_count = 0
    st.session_state.withheld_count = 0

    st.rerun()


# ============================================================
# GENERATE + REVIEW QUESTION
# ============================================================

def generate_current_question():
    index = st.session_state.question_index
    questions = st.session_state.targets

    if index < len(questions):
        st.session_state.current_item = questions[index]
        st.session_state.answered = False
        st.session_state.selected_answer = None

def next_question():
    st.session_state.question_index += 1
    st.session_state.current_item = None
    st.session_state.answered = False
    st.session_state.selected_answer = None
    st.rerun()


# ============================================================
# FULL EOC PRACTICE
# ============================================================

if st.session_state.mode is None:
    start_session(
        "taylisha",
        "Taylisha - Missed Question Practice",
    )
    


# ============================================================
# SESSION HEADER
# ============================================================

total_questions = len(st.session_state.targets)

current_number = min(
    st.session_state.question_index + 1,
    total_questions,
)

top1, top2, top3, top4 = st.columns(4)

top1.metric(
    "Question",
    f"{current_number} / {total_questions}",
)

top2.metric(
    "Answered",
    st.session_state.answered_count,
)

top3.metric(
    "Correct",
    st.session_state.score,
)

if st.session_state.answered_count:
    percentage = round(
        (
            st.session_state.score
            / st.session_state.answered_count
        )
        * 100
    )
else:
    percentage = 0

top4.metric(
    "Score",
    f"{percentage}%",
)

st.progress(
    min(
        st.session_state.question_index
        / max(total_questions, 1),
        1.0,
    )
)

st.caption(st.session_state.mode)

st.divider()


# ============================================================
# SESSION COMPLETE
# ============================================================

if st.session_state.question_index >= total_questions:

    st.success("Practice session complete.")

    st.subheader(
        f"Final Score: "
        f"{st.session_state.score} / "
        f"{st.session_state.answered_count}"
    )

    if st.session_state.answered_count:

        final_percentage = round(
            (
                st.session_state.score
                / st.session_state.answered_count
            )
            * 100
        )

        st.metric(
            "Percentage",
            f"{final_percentage}%",
        )

    if st.session_state.withheld_count:
        st.info(
            f"{st.session_state.withheld_count} target(s) "
            "were withheld by clinical review."
        )

    if st.button("Return to Practice Modes"):
        st.session_state.mode = None
        st.session_state.current_item = None
        st.rerun()

    st.stop()


# ============================================================
# GENERATE QUESTION IF NEEDED
# ============================================================

if st.session_state.current_item is None:

    generate_current_question()

    if st.session_state.current_item is None:
        st.rerun()


item = st.session_state.current_item


# ============================================================
# TARGET INFORMATION
# ============================================================

with st.expander(
    "Question Details",
    expanded=False,
):

    detail1, detail2, detail3 = st.columns(3)

    detail1.write(
        f"**Content Area:** {item.content_area}"
    )

    detail2.write(
        f"**Task:** {item.task}"
    )

    detail3.write(
        f"**Topic:** {item.topic}"
    )

    detail1.write(
        f"**Setting:** {item.setting}"
    )

    detail2.write(
        f"**Life Course:** {item.life_course}"
    )

    detail3.write(
        f"**Cognitive Level:** {item.cognitive_level}"
    )


# ============================================================
# QUESTION
# ============================================================

st.subheader(
    f"Question {current_number}"
)

st.markdown("### Vignette")

st.write(item.vignette)

st.markdown("### Question")

st.write(item.lead_in)

st.write("")


# ============================================================
# ANSWER BUTTONS
# ============================================================

for choice in item.answer_choices:

    label = f"{choice.letter}. {choice.text}"

    if st.button(
        label,
        key=f"answer_{current_number}_{choice.letter}",
        use_container_width=True,
        disabled=st.session_state.answered,
    ):

        st.session_state.selected_answer = choice.letter
        st.session_state.answered = True
        st.session_state.answered_count += 1

        if choice.letter == item.correct_answer:
            st.session_state.score += 1

        st.rerun()


# ============================================================
# RESULTS
# ============================================================

if st.session_state.answered:

    st.divider()

    selected = st.session_state.selected_answer
    correct = item.correct_answer

    correct_choice = next(
        choice
        for choice in item.answer_choices
        if choice.letter == correct
    )

    if selected == correct:

        st.success(
            f"Correct — {correct}. "
            f"{correct_choice.text}"
        )

    else:

        st.error(
            f"Incorrect — Correct answer: "
            f"{correct}. {correct_choice.text}"
        )

    st.markdown("### Rationale")
    st.write(item.rationale)

    st.markdown("### Why the other choices are wrong")

    for explanation in item.distractor_rationales:
        st.markdown(
            f"**{explanation.letter}.** {explanation.explanation}"
        )

    st.markdown("### Teaching Point")
    st.info(item.teaching_point)

    st.divider()

    if st.button(
        "Next Question →",
        type="primary",
        use_container_width=True,
    ):
        next_question()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Session")

    st.write(
        f"**Mode:** {st.session_state.mode}"
    )

    st.write(
        f"**Answered:** "
        f"{st.session_state.answered_count}"
    )

    st.write(
        f"**Correct:** {st.session_state.score}"
    )

    st.write(
        f"**Withheld:** "
        f"{st.session_state.withheld_count}"
    )

    st.divider()

    if st.button(
        "End Session",
        use_container_width=True,
    ):
        st.session_state.mode = None
        st.session_state.targets = []
        st.session_state.current_item = None
        st.session_state.question_index = 0
        st.session_state.answered = False
        st.session_state.selected_answer = None
        st.session_state.score = 0
        st.session_state.answered_count = 0
        st.session_state.withheld_count = 0
        st.rerun()
