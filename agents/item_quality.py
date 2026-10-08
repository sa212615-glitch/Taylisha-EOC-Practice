"""Review the exact randomized item that will be presented to the learner."""
import random
import re

from agents.clinical_reviewer import review_item
from agents.item_reviser import EOCItem, revise_item

CHECKS = (
    "medically_accurate", "one_best_answer", "task_aligned",
    "vignette_consistent", "rationale_accurate", "distractors_plausible",
)


def shuffle_choices(item, rng=None):
    """Relabel choices and their key/rationale identities without mutating input."""
    data = item.model_dump()
    letters = list("ABCDE")
    choices = data["answer_choices"]
    old_letters = [c["letter"].strip().upper() for c in choices]
    correct = data["correct_answer"].strip().upper()
    explanations = data["distractor_rationales"]
    explanation_letters = [r["letter"].strip().upper() for r in explanations]
    if sorted(old_letters) != letters or correct not in letters:
        raise ValueError("The item needs five unique A-E choices and a valid answer letter.")
    if sorted(explanation_letters) != [x for x in letters if x != correct]:
        raise ValueError("Each incorrect choice must have exactly one explanation.")
    for choice, letter in zip(choices, old_letters):
        choice["letter"] = letter
    (rng or random).shuffle(choices)
    mapping = {choice["letter"]: new for new, choice in zip(letters, choices)}

    # Remap explicit references only: do not corrupt articles or clinical values
    # such as 'A patient', vitamin A, hepatitis B, or a laboratory grade.
    reference = re.compile(r"\b((?:option|choice|answer)\s+)([A-E])\b", re.I)
    def relabel_text(text):
        return reference.sub(lambda m: m[1] + mapping[m[2].upper()], text)

    for new, choice in zip(letters, choices):
        choice["letter"] = new
        choice["text"] = relabel_text(choice["text"])
    data["correct_answer"] = mapping[correct]
    for explanation in explanations:
        explanation["letter"] = mapping[explanation["letter"].strip().upper()]
        explanation["explanation"] = relabel_text(explanation["explanation"])
    explanations.sort(key=lambda r: r["letter"])
    for field in ("vignette", "lead_in", "rationale", "teaching_point"):
        data[field] = relabel_text(data[field])
    return EOCItem.model_validate(data)


def approve_item(item, save, max_revisions=2):
    """Return a reviewed item or None. At most two revisions and three reviews."""
    target = {k: getattr(item, k) for k in
              ("content_area", "task", "topic", "life_course", "cognitive_level")}
    history = []
    for attempt in range(max_revisions + 1):
        if any(getattr(item, key) != value for key, value in target.items()):
            print("Item withheld: revision changed the assigned target or context.")
            return None
        try:
            candidate = shuffle_choices(item)
        except ValueError as error:
            print(f"Item withheld: {error}")
            return None
        # Review AFTER randomization, including all prose references to letters.
        review = review_item(candidate.model_dump())
        save(review, "latest_review.json")
        history.append({"attempt": attempt, "item": candidate.model_dump(),
                        "review": review.model_dump()})
        save(history, "latest_review_history.json")
        verdict = review.overall_verdict.strip().upper()
        consistent_pass = (
            verdict == "PASS" and review.severity.strip().upper() == "PASS"
            and all(getattr(review, check) is True for check in CHECKS)
            and not review.issues and not review.recommended_changes
        )
        print(f"Review {attempt + 1}: {verdict}")
        if consistent_pass:
            return candidate
        if verdict not in ("PASS", "REVISE"):
            print("Item withheld: rejected or unrecognized review verdict.")
            return None
        if attempt == max_revisions:
            print("Item withheld: review concerns remain after two revisions.")
            return None
        print("Revising item; another review is required before display.")
        item = revise_item(candidate.model_dump(), review.model_dump())
    return None
