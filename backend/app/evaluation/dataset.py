import json

DEFAULT_PATH = "../data/evaluation/questions.json"


def load_questions(path: str = DEFAULT_PATH) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)