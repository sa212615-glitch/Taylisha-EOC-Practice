import json
import random
from pathlib import Path

from agents.item_generator import load_targets, generate_item
from agents.item_quality import approve_item


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def save_json(data, filename):
    path = OUTPUT_DIR / filename

    if hasattr(data, "model_dump"):
        data = data.model_dump()

    with open(path, "w") as file:
        json.dump(data, file, indent=2)

    return path


def display_question(item):
    print("\n" + "=" * 70)
    print("AI REVIEWED PRACTICE ITEM")
    print("=" * 70)

    print(f"\nContent Area: {item.content_area}")
    print(f"Task: {item.task}")
    print(f"Topic: {item.topic}")
    print(f"Setting: {item.setting}")
    print(f"Life Course: {item.life_course}")
    print(f"Cognitive Level: {item.cognitive_level}")

    print("\nVIGNETTE")
    print(item.vignette)

    print("\nQUESTION")
    print(item.lead_in)

    print()

    for choice in item.answer_choices:
        print(f"{choice.letter}. {choice.text}")



def select_eoc_context(topic):
    # Choose a clinically appropriate setting based on topic
    emergency_topics = {
        "Unstable angina",
        "Cardiac tamponade",
        "Ventricular fibrillation",
        "Intussusception",
        "Acute appendicitis",
    }

    outpatient_topics = {
        "Hypertension",
        "Hashimoto thyroiditis",
        "Primary hyperparathyroidism",
        "Atrial fibrillation",
        "Aortic stenosis",
    }

    if topic in emergency_topics:
        setting = random.choices(
            ["Emergency Department", "Inpatient"],
            weights=[85, 15],
            k=1,
        )[0]
    elif topic in outpatient_topics:
        setting = random.choices(
            ["Outpatient", "Inpatient"],
            weights=[90, 10],
            k=1,
        )[0]
    else:
        setting = random.choices(
            [
                "Outpatient",
                "Inpatient",
                "Emergency Department",
                "Perioperative",
                "Rehabilitation",
            ],
            weights=[50, 20, 20, 8, 2],
            k=1,
        )[0]


    # Choose life course based on whether the topic is primarily pediatric
    pediatric_topics = {
        "Tricuspid atresia",
        "Truncus arteriosus",
        "Tetralogy of Fallot",
        "Acute rheumatic fever",
        "Hand-foot-and-mouth disease",
        "Mastoiditis",
        "Hirschsprung disease",
        "Intussusception",
        "Pyloric stenosis",
        "Acute bronchiolitis",
        "Pilocytic astrocytoma",
    }
    
    if topic in pediatric_topics:
        life_course = random.choices(
            ["Pediatric", "Adult"],
            weights=[90, 10],
            k=1,
        )[0]
    else:
        life_course = random.choices(
            ["Pediatric", "Adult", "Geriatric"],
            weights=[20, 60, 20],
            k=1,
        )[0]

    cognitive_level = random.choices(
        [
            "Understand and Apply",
            "Analyze and Evaluate",
            "Remember",
        ],
        weights=[50, 40, 10],
        k=1,
    )[0]

    return setting, life_course, cognitive_level

def main():
    print("\nPA EOC ITEM GENERATOR")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. SELECT TARGET
    # ---------------------------------------------------------

    print("\nChoose practice mode:")
    print("1. Full EOC Practice")
    print("2. Catherine - Missed Question Practice")
    print("3. Yesenia - Missed Question Practice")

    while True:
        practice_mode = input("\nEnter 1, 2, or 3: ").strip()

        if practice_mode == "1":
            targets = load_targets("eoc")
            session_targets = [random.choice(targets)]
            print("\nFull EOC Practice selected.")
            break

        elif practice_mode == "2":
            targets = load_targets("catherine")
            session_targets = targets.copy()
            random.shuffle(session_targets)
            print(f"\nCatherine selected: {len(session_targets)} questions, no repeats.")
            break

        elif practice_mode == "3":
            targets = load_targets("yesenia")
            session_targets = targets.copy()
            random.shuffle(session_targets)
            print(f"\nYesenia selected: {len(session_targets)} questions, no repeats.")
            break

        else:
            print("Please enter 1, 2, or 3.")


    total_questions = len(session_targets)
    displayed_count = 0
    withheld_count = 0

    for question_number, target in enumerate(session_targets, start=1):
        print("\n" + "=" * 70)
        print(f"QUESTION {question_number} OF {total_questions}")
        print("=" * 70)
        setting, life_course, cognitive_level = select_eoc_context(target["topic"])
    
        print("\nSelected target:")
        print(f"  Content Area: {target['content_area']}")
        print(f"  Task: {target['task']}")
        print(f"  Topic: {target['topic']}")
    
        # ---------------------------------------------------------
        # 2. GENERATE
        # ---------------------------------------------------------
    
        max_generation_attempts = 3
        final_item = None

        for generation_attempt in range(1, max_generation_attempts + 1):
            if generation_attempt == 1:
                print("\n[1/3] Generating item...")
            else:
                print(
                    f"\nRegenerating SAME target "
                    f"(attempt {generation_attempt}/{max_generation_attempts})..."
                )

            generated_item = generate_item(
                target,
                setting=setting,
                life_course=life_course,
                cognitive_level=cognitive_level,
            )

            save_json(generated_item, "latest_item.json")
            print("Generation complete.")

            # --------------------------------------------------------
            # 3. CLINICAL REVIEW
            # --------------------------------------------------------

            print("\n[2/3] Running independent clinical review...")

            (OUTPUT_DIR / "final_item.json").unlink(missing_ok=True)
            (OUTPUT_DIR / "latest_review.json").unlink(missing_ok=True)
            (OUTPUT_DIR / "latest_review_history.json").unlink(missing_ok=True)

            final_item = approve_item(generated_item, save_json)

            if final_item is not None:
                break

            if generation_attempt < max_generation_attempts:
                print("Item withheld. Regenerating the SAME target.")

        if final_item is None:
            withheld_count += 1
            print(
                f"Target withheld after {max_generation_attempts} "
                "complete generation attempts."
            )
            continue

        # ---------------------------------------------------------
        # 5. SAVE FINAL ITEM
        # ---------------------------------------------------------
    
        final_path = save_json(
            final_item,
            "final_item.json"
        )
    
        print(f"\nAI-reviewed item saved to:\n{final_path}")
    
        # ---------------------------------------------------------
        # 6. DISPLAY QUESTION ONLY
        # ---------------------------------------------------------
    
        displayed_count += 1
        display_question(final_item)
    
        print("\n" + "-" * 70)
    
        valid_answers = {"A", "B", "C", "D", "E"}
    
        while True:
            user_answer = input("Your answer (A-E): ").strip().upper()
    
            if user_answer in valid_answers:
                break
    
            print("Please enter A, B, C, D, or E.")
    
        correct_letter = final_item.correct_answer.strip().upper()
    
        if user_answer == correct_letter:
            print("\nCORRECT")
        else:
            print(f"\nINCORRECT — Correct answer: {correct_letter}")
    
        correct_choice = next(
            choice for choice in final_item.answer_choices
            if choice.letter.upper() == correct_letter
        )
    
        print(f"\n{correct_letter}. {correct_choice.text}")
    
        print("\nRATIONALE")
        print(final_item.rationale)
    
        print("\nWHY THE OTHER CHOICES ARE WRONG")
    
        for distractor in final_item.distractor_rationales:
            print(f"{distractor.letter}: {distractor.explanation}")
    
        print("\nTEACHING POINT")
        print(final_item.teaching_point)
    
        print("\n" + "-" * 70)
    
    
    print(f"\nSession complete: {displayed_count} answered; {withheld_count} withheld.")


if __name__ == "__main__":
    main()
