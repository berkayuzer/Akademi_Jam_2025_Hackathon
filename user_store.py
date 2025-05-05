# user_store.py
import os
import json
from typing import Dict

USER_DB_FILE = "users.json"

def load_users() -> Dict[str, dict]:
    if not os.path.exists(USER_DB_FILE):
        return {}
    with open(USER_DB_FILE, "r") as f:
        return json.load(f)

def save_users(users: Dict[str, dict]):
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f)
