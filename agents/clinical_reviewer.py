import json
from pathlib import Path
from typing import List

from langchain_openai import ChatOpenAI
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent.parent


class ClinicalReview(BaseModel):
    medically_accurate: bool
    one_best_answer: bool
    task_aligned: bool
    vignette_consistent: bool
    rationale_accurate: bool
    distractors_plausible: bool

    severity: str
    issues: List[str]
    recommended_changes: List[str]
    overall_verdict: str


REVIEW_PROMPT = """
You are the clinical accuracy reviewer for a physician assistant
medical assessment item.

Independently evaluate the supplied multiple-choice question.

Do not assume the proposed correct answer is correct.

Review the item for:

1. Medical and scientific accuracy.
2. Whether the proposed correct answer is truly the single best answer.
3. Whether another answer choice could also reasonably be correct.
4. Whether the vignette contains contradictory or misleading information.
5. Whether the question actually assesses the assigned task.
6. Whether the rationale accurately explains the answer.
7. DISTRACTOR QUALITY:
   Evaluate EACH incorrect answer choice individually.
   - Every distractor must be clinically plausible in the context of the vignette and lead-in.
   - Every distractor must represent a reasonable competing diagnosis, finding, risk factor, diagnostic test, treatment, or mechanism relevant to the clinical problem being tested.
   - Reject distractors that are unrelated to the organ system, presentation, or clinical decision being tested.
   - Reject obvious throwaway choices that a learner could eliminate without medical knowledge or clinical reasoning.
   - Reject distractors that introduce symptoms, diseases, historical features, or clinical concepts with no reasonable relationship to the vignette.
   - Distractors should preferably represent common misconceptions, closely competing diagnoses, partially compatible findings, or reasonable alternatives that become incorrect only after interpreting the vignette carefully.
   - For diagnosis questions, distractors should come from the realistic differential diagnosis.
   - For history/physical questions, distractors should be plausible findings or risk factors associated with reasonable competing conditions.
   - For diagnostic-study questions, distractors should be tests that could reasonably be considered for the presentation.
   - For treatment questions, distractors should be treatments that could reasonably be considered in related clinical situations.
   - If ANY distractor is obviously irrelevant, absurd, or substantially easier to eliminate than the others, set distractors_plausible to false and recommend replacement.
   - Do not approve an item merely because the correct answer is accurate; all four distractors must also meet these standards.
8. Whether management, diagnostic, screening, or treatment claims could
   depend on guideline-specific details that require verification.
9. Whether the item genuinely matches the assigned cognitive level.

COGNITIVE LEVEL VALIDATION:

Remember:
The item may primarily require recall or recognition of a fact, association,
classic finding, definition, or first-line fact.

Understand and Apply:
The item must require interpretation of a clinical presentation and
application of medical knowledge. The answer should not depend only on
direct recall of an isolated fact.

Analyze and Evaluate:
The item must require integration of multiple clinically relevant findings
and meaningful discrimination among plausible alternatives. The examinee
should need to interpret the significance of findings, compare competing
possibilities, or determine the best answer after considering those
possibilities.

IMPORTANT:
Do not judge cognitive level from vignette length or the number of facts
provided. Judge the reasoning actually required to answer the question.

For an item assigned "Analyze and Evaluate", require revision if:
- one classic or pathognomonic clue essentially reveals the answer;
- several clues redundantly point to the same obvious answer without
  requiring meaningful discrimination;
- the distractors can be eliminated without integrating the clinical data;
- the item functions primarily as recognition, recall, or straightforward
  application despite being labeled Analyze and Evaluate.

For an item assigned "Understand and Apply", require revision if the item
functions primarily as simple recall or recognition.

A cognitive-level mismatch is a substantive item-quality problem.
Recommend revision so the reasoning demand matches the assigned level.

The choices may have been shuffled. Check that the correct-answer letter,
all distractor-rationale letters, and every letter reference in the prose
match the choices as currently displayed. Treat stale references (including
bare letters or references to the first/last option) as requiring revision.
Check that option ordering does not create an invalid or ambiguous item.

TASK DEFINITIONS:

History and Physical:
The item should assess clinically important history or examination findings.

Diagnostic Studies:
The item should assess selection or interpretation of diagnostic testing,
not merely identification of the diagnosis.

Diagnosis:
The item should assess identification of the most likely diagnosis.

Clinical Intervention:
The item should assess an appropriate procedure, immediate intervention,
disposition, or other clinical action.

Clinical Therapeutics:
The item should assess therapeutic management.

Health Maintenance:
The item should assess prevention, screening, vaccination, counseling,
or longitudinal health maintenance.

Scientific Concepts:
The item should assess an underlying scientific concept.

Professional Practice:
The item should assess patient safety, communication, ethics,
systems-based practice, professional responsibility, or evidence-based practice.

SEVERITY:

PASS:
No meaningful clinical problem.

MINOR:
The item remains answerable but wording or precision should be improved.

MAJOR:
MAJOR:
A medical error, ambiguity, task mismatch, cognitive-level mismatch,
multiple defensible answers, or other problem makes the item unsuitable
without revision.

Be critical. Do not approve an item merely because it sounds medically plausible.
"""


def load_item():
    path = BASE_DIR / "output" / "latest_item.json"

    with open(path, "r") as file:
        return json.load(file)


def review_item(item):
    model = ChatOpenAI(
        model="gpt-5.4-mini",
        temperature=0,
    )

    reviewer = model.with_structured_output(ClinicalReview)

    request = f"""
Review the following generated PA assessment item.

ITEM:

{json.dumps(item, indent=2)}

Return an independent clinical review.

For overall_verdict, use one of:
PASS
REVISE
REJECT

If there are no meaningful issues, return empty lists for issues and
recommended_changes.
"""

    return reviewer.invoke(
        [
            ("system", REVIEW_PROMPT),
            ("human", request),
        ]
    )


if __name__ == "__main__":
    item = load_item()
    review = review_item(item)

    print("\n" + "=" * 70)
    print("CLINICAL REVIEW")
    print("=" * 70)

    print("\nMedically Accurate:", review.medically_accurate)
    print("One Best Answer:", review.one_best_answer)
    print("Task Aligned:", review.task_aligned)
    print("Vignette Consistent:", review.vignette_consistent)
    print("Rationale Accurate:", review.rationale_accurate)
    print("Distractors Plausible:", review.distractors_plausible)

    print("\nSeverity:", review.severity)
    print("Verdict:", review.overall_verdict)

    print("\nISSUES")
    if review.issues:
        for issue in review.issues:
            print("-", issue)
    else:
        print("- None")

    print("\nRECOMMENDED CHANGES")
    if review.recommended_changes:
        for change in review.recommended_changes:
            print("-", change)
    else:
        print("- None")

    output_file = BASE_DIR / "output" / "latest_review.json"

    with open(output_file, "w") as file:
        json.dump(review.model_dump(), file, indent=2)

    print(f"\nSaved review to: {output_file}")
