import json
from pathlib import Path


DATA_FILE = Path("u9_data.json")

def _ensure_structure(data):
    if "players" not in data:
        data["players"] = []
    if "matches" not in data:
        data["matches"] = []
    if "trainings" not in data:
        data["trainings"] = []
    return data


def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    return _ensure_structure(data)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_next_id(items):
    if not items:
        return 1
    return max(item["id"] for item in items) + 1


def find_player(data, player_id):
    for player in data["players"]:
        if player["id"] == player_id:
            return player
    return None


def find_match(data, match_id):
    for match in data["matches"]:
        if match["id"] == match_id:
            return match
    return None


def find_training(data, training_id):
    for training in data["trainings"]:
        if training["id"] == training_id:
            return training
    return None
