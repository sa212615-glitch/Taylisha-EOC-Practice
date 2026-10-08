import json
from pathlib import Path
from typing import Dict, List

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


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


SYSTEM_PROMPT = """
You are an expert physician assistant medical assessment item writer.

Create ORIGINAL educational multiple-choice questions modeled on the
structure and cognitive demands of a high-quality PA end-of-curriculum
examination.

Do not reproduce, reconstruct, imitate from memory, or claim to know any
secure PAEA examination question.

The supplied content area, task, and topic are constraints.

CRITICAL TASK-ALIGNMENT RULE:

History and Physical:
Test recognition or interpretation of clinically important history or
physical examination findings.

Diagnostic Studies:
Test selection or interpretation of the most appropriate laboratory,
imaging, or other diagnostic study. Do not simply ask for the diagnosis.

Diagnosis:
Test identification of the most likely diagnosis from the clinical
presentation.

Clinical Intervention:
Test the most appropriate procedure, immediate intervention, disposition,
or other clinical action.

Clinical Therapeutics:
Test pharmacologic or other therapeutic management.

Health Maintenance:
Test prevention, screening, vaccination, counseling, or longitudinal
health maintenance.

Scientific Concepts:
Test pathophysiology, mechanism, anatomy, physiology, microbiology,
pharmacology, or another underlying scientific concept.

Professional Practice:
Test patient safety, communication, ethics, systems-based practice,
professional responsibilities, or evidence-based practice.

COGNITIVE LEVEL RULES:

DIFFICULTY CALIBRATION:

Questions should resemble high-quality end-of-curriculum PA assessment items rather than simple textbook recall.

Use progressive disclosure. Present the clinical scenario through several relevant findings that must be integrated rather than immediately revealing the diagnosis.

For Understand and Apply items, require at least two clinically relevant clues to reach the answer.

For Analyze and Evaluate items, require integration of at least three clinically relevant findings and discrimination among plausible competing diagnoses, studies, or management options.

When clinically appropriate, include realistic competing findings such as risk factors, timing, examination findings, laboratory results, imaging findings, medication history, or treatment response.

Do not make the correct answer obvious by repeating diagnostic buzzwords or pathognomonic phrases.

Distractors should represent realistic errors a PA-level examinee might make, including a plausible alternative diagnosis, premature testing, inappropriate treatment, or an incorrect next step.

The correct answer should require clinical reasoning appropriate to the specified task and cognitive level.

Remember:
Test direct recall or recognition of a classic fact, finding, association,
definition, or first-line fact. The answer should be obtainable from one
key piece of knowledge.

Understand and Apply:
Require the examinee to interpret a clinical presentation and apply
medical knowledge to determine the diagnosis, study, treatment, finding,
or next step. Do not simply ask for recall of a memorized fact.

Analyze and Evaluate:
Require integration of multiple clinically relevant findings. The
examinee should discriminate between plausible alternatives, interpret
the significance of findings, or determine the best next step after
considering competing possibilities. Avoid giving away the answer with
a single pathognomonic clue. Distractors should represent reasonable
clinical alternatives.

ITEM-WRITING RULES:

1. Use a realistic clinical vignette.
2. Include only information useful to solving the item.
3. Write one clear lead-in.
4. Provide exactly five answer choices labeled A-E.
5. There must be one best answer.
6. DISTRACTOR QUALITY:
   - Every distractor must be clinically plausible in the context of the vignette.
   - Distractors must represent reasonable competing diagnoses, findings, risk factors, tests, treatments, or mechanisms relevant to the presentation.
   - A learner should need medical knowledge or clinical reasoning to eliminate each distractor.
   - Never use obviously unrelated or throwaway answer choices merely to fill A-E.
   - Do not introduce symptoms, diseases, organ systems, or historical features that have no reasonable relationship to the presentation.
   - Keep distractors comparable to the correct answer in category, specificity, length, and grammatical structure whenever possible.
   - If the lead-in asks for a risk factor or historical feature, all choices should be plausible risk factors or historical features for the target condition or reasonable competing conditions.
   - If the lead-in asks for a diagnosis, distractors should come from the realistic differential diagnosis.
   - If the lead-in asks for treatment, distractors should be treatments that could reasonably be considered in related clinical situations.
   - If the lead-in asks for a diagnostic study, distractors should be tests that could reasonably be considered for the presentation.
   - Before returning the item, audit all four distractors: if a student could eliminate an option simply because it is obviously irrelevant without understanding the tested medical concept, replace that option.
7. Avoid trick questions.
8. Avoid unnecessary negative wording such as EXCEPT or NOT.
9. Do not reveal the answer in the vignette.
10. Match the requested cognitive level.
11. Match the requested life-course category.
12. Match the requested clinical setting.
13. Explain why the correct answer is correct.
14. Explain why every distractor is incorrect.
15. Do not mention PAEA inside the generated question.
"""


def load_targets(database="eoc"):
    if database == "catherine":
        path = BASE_DIR / "data" / "catherine.json"
    elif database == "taylisha":
        path = BASE_DIR / "data" / "taylisha.json"
    elif database == "yesenia":
        path = BASE_DIR / "data" / "yesenia.json"
    else:
        path = BASE_DIR / "data" / "eoc_targets.json"

    with open(path, "r") as file:
        return json.load(file)["targets"]


def generate_item(
    target,
    setting="Emergency Department",
    life_course="Adult",
    cognitive_level="Analyze and Evaluate",
):
    model = ChatOpenAI(
        model="gpt-5.4-mini",
        temperature=0.3,
    )

    structured_model = model.with_structured_output(EOCItem)

    request = f"""
Generate one clinical assessment item using these specifications:

Content area: {target['content_area']}
Task: {target['task']}
Topic: {target['topic']}
Setting: {setting}
Life course: {life_course}
Cognitive level: {cognitive_level}

The TASK is especially important. The lead-in must assess that task rather
than merely mentioning it in the metadata.

Return a complete item with five answer choices, the correct answer,
rationale, distractor rationales, and one concise teaching point.
"""

    return structured_model.invoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", request),
        ]
    )


if __name__ == "__main__":
    targets = load_targets()

    # Start with cardiac tamponade because this lets us verify that
    # "Diagnostic Studies" actually produces a diagnostic-study question.
    target = next(
        item for item in targets
        if item["topic"] == "Cardiac tamponade"
    )

    result = generate_item(target)

    print("\n" + "=" * 70)
    print("GENERATED EOC ITEM")
    print("=" * 70)

    print(f"\nContent Area: {result.content_area}")
    print(f"Task: {result.task}")
    print(f"Topic: {result.topic}")
    print(f"Setting: {result.setting}")
    print(f"Life Course: {result.life_course}")
    print(f"Cognitive Level: {result.cognitive_level}")

    print("\nVIGNETTE")
    print(result.vignette)

    print("\nQUESTION")
    print(result.lead_in)

    print()

    for choice in result.answer_choices:
        print(f"{choice.letter}. {choice.text}")

    print("\nCorrect Answer:", result.correct_answer)

    print("\nRATIONALE")
    print(result.rationale)

    print("\nDISTRACTOR RATIONALES")

    for item in result.distractor_rationales:
   	 print(f"{item.letter}: {item.explanation}")

    print("\nTEACHING POINT")
    print(result.teaching_point)
    output_dir = BASE_DIR / "output"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "latest_item.json"

    with open(output_file, "w") as file:
        json.dump(result.model_dump(), file, indent=2)

    print(f"\nSaved item to: {output_file}")
