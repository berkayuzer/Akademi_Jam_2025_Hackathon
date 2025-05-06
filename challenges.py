import json
from typing import List, Dict
import os

CHALLENGES_FILE = "challenges.json"

def load_challenges() -> List[Dict]:
    if not os.path.exists(CHALLENGES_FILE):
        return []
    with open(CHALLENGES_FILE, "r") as f:
        return json.load(f)

def save_challenges(challenges: List[Dict]):
    with open(CHALLENGES_FILE, "w") as f:
        json.dump(challenges, f, indent=2)

def get_challenge_by_id(challenge_id: str) -> Dict:
    challenges = load_challenges()
    for challenge in challenges:
        if challenge["id"] == challenge_id:
            return challenge
    return None