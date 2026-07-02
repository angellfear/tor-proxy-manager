import json
import hashlib
import secrets
from pathlib import Path

USERS_PATH = Path('/config/users.json')

def load_users():
    if USERS_PATH.exists():
        with open(USERS_PATH) as f:
            return json.load(f)
    return {}

def save_users(users):
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(USERS_PATH, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f'{salt}:{h}'

def verify_password(stored, password):
    salt, h = stored.split(':', 1)
    return hashlib.sha256((salt + password).encode()).hexdigest() == h

def authenticate(username, password):
    users = load_users()
    if username in users:
        stored = users[username].get('password', '')
        if verify_password(stored, password):
            return True
    return False

def change_password(username, old_pw, new_pw):
    users = load_users()
    if username not in users:
        return False
    stored = users[username].get('password', '')
    if not verify_password(stored, old_pw):
        return False
    users[username]['password'] = hash_password(new_pw)
    save_users(users)
    return True
