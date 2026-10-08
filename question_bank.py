import json
from pathlib import Path

from agents.item_generator import EOCItem

BANK_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "question_bank"
    / "taylisha_questions.json"
)

def load_question_bank():
    with BANK_PATH.open() as file:
        data = json.load(file)

    return [
        EOCItem.model_validate(question)
        for question in data["questions"]
    ]
