import json
import os
import random
import sys
from pathlib import Path

from agents.item_generator import load_targets, generate_item
from agents.item_quality import approve_item
from app import save_json, select_eoc_context

BANK_PATH = Path("data/question_bank/taylisha_questions.json")
MAX_ATTEMPTS = 3


def save_bank(questions):
    """Save approved questions safely after each addition."""
    BANK_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = BANK_PATH.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"questions": questions}, indent=2)
    )
    temporary.replace(BANK_PATH)


def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OpenAI API key is not configured.")
        return

    targets = load_targets("taylisha")

    if BANK_PATH.exists():
        questions = json.loads(
            BANK_PATH.read_text()
        )["questions"]
    else:
        questions = []

    completed = {
        (
            q["content_area"],
            q["task"],
            q["topic"],
        )
        for q in questions
    }

    remaining = [
        target
        for target in targets
        if (
            target["content_area"],
            target["task"],
            target["topic"],
        ) not in completed
    ]

    random.shuffle(remaining)
    if "--test" in sys.argv:
        remaining = remaining[:1]

    print(f"Targets: {len(targets)}")
    print(f"Already saved: {len(questions)}")
    print(f"Remaining: {len(remaining)}")

    for index, target in enumerate(remaining, 1):
        print(
            f"\n[{index}/{len(remaining)}] "
            f"{target['topic']} — {target['task']}",
            flush=True,
        )

        setting, life_course, cognitive_level = (
            select_eoc_context(target["topic"])
        )

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                print(
                    f"Generating and reviewing "
                    f"(attempt {attempt}/{MAX_ATTEMPTS})...",
                    flush=True,
                )

                generated = generate_item(
                    target,
                    setting=setting,
                    life_course=life_course,
                    cognitive_level=cognitive_level,
                )

                approved = approve_item(
                    generated,
                    save_json,
                )

                if approved is None:
                    print("Not approved. Retrying...")
                    continue

                question = approved.model_dump()

                questions.append(question)
                save_bank(questions)

                print(
                    f"APPROVED AND SAVED — "
                    f"Total: {len(questions)}",
                    flush=True,
                )
                break

            except Exception as error:
                print(
                    f"Error: {error}",
                    flush=True,
                )

        else:
            print(
                "Target not approved after 3 attempts. "
                "Skipping for now.",
                flush=True,
            )

    print(
        f"\nFinished. Saved questions: {len(questions)}"
    )


if __name__ == "__main__":
    main()
