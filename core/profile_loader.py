import json
from pathlib import Path


def load_profile(path: str = "data/profile_data.json") -> dict:
    profile_path = Path(path)

    if not profile_path.exists():
        raise FileNotFoundError(f"Profile file not found: {path}")

    with profile_path.open("r", encoding="utf-8") as file:
        return json.load(file)