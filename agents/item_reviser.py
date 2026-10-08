import json
from pathlib import Path
from typing import Dict, List

from langchain_openai import ChatOpenAI
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent.parent


class AnswerChoice(BaseModel):
    letter: str
    text: str


class DistractorRationale(BaseModel):
    letter: str
    explanation: str


class EOCItem(BaseModel):
    content_area: str
    task: str
    topic: str
    setting: str
    life_course: str
    cognitive_level: str

    vignette: str
    lead_in: str

    answer_choices: List[AnswerChoice]
    correct_answer: str

    rationale: str
    distractor_rationales: List[DistractorRationale]

    teaching_point: str


REVISION_PROMPT = """
You are a senior physician assistant medical assessment item editor.

You will receive:
1. An original clinical multiple-choice item.
2. An independent clinical review of that item.

Revise the item only as necessary to correct the reviewer's concerns.

REQUIREMENTS:

- Preserve the assigned content area.
- Preserve the assigned topic.
- Preserve the assigned task.
- Preserve the original clinical setting exactly. Do not change it during revision.
- Preserve the life-course category.
- Preserve the cognitive level.

The final item must:

1. Be medically accurate.
2. Have exactly one best answer.
3. Contain exactly five answer choices labeled A-E.
4. Use clinically plausible distractors.
5. Have a clear lead-in.
6. Assess the assigned task.
7. Avoid trick wording.
8. Avoid unnecessary clues to the correct answer.
9. Include an accurate rationale.
10. Explain why each distractor is incorrect.
11. Be an ORIGINAL educational item.
12. Refer to answer content rather than choice letters or positions in prose;
    choices will be shuffled and reviewed again before display.

Do not reproduce or attempt to reconstruct secure examination questions.

If the reviewer marked the item PASS and identified no meaningful problems,
preserve the item rather than changing it unnecessarily.
"""


def load_json(filename):
    path = BASE_DIR / "output" / filename

    with open(path, "r") as file:
        return json.load(file)


def revise_item(item, review):
    model = ChatOpenAI(
        model="gpt-5.4-mini",
        temperature=0.2,
    )

    reviser = model.with_structured_output(EOCItem)

    request = f"""
ORIGINAL ITEM:

{json.dumps(item, indent=2)}

CLINICAL REVIEW:

{json.dumps(review, indent=2)}

Produce the final corrected assessment item.
"""

    return reviser.invoke(
        [
            ("system", REVISION_PROMPT),
            ("human", request),
        ]
    )


if __name__ == "__main__":
    item = load_json("latest_item.json")

    # Use the same bounded review gate as the interactive application.
    import sys
    sys.path.insert(0, str(BASE_DIR))
    from agents.item_quality import approve_item

    def save_snapshot(value, filename):
        if hasattr(value, "model_dump"):
            value = value.model_dump()
        with open(BASE_DIR / "output" / filename, "w") as file:
            json.dump(value, file, indent=2)

    output_file = BASE_DIR / "output" / "final_item.json"
    output_file.unlink(missing_ok=True)
    final_item = approve_item(EOCItem.model_validate(item), save_snapshot)
    if final_item is None:
        print("No approved item saved.")
    else:
        save_snapshot(final_item, "final_item.json")
        print(f"AI-reviewed item saved to: {output_file}")
