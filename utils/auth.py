# utils/auth.py
import hashlib
from utils.constants import USERS


def verify_login(username: str, password: str) -> tuple[bool, dict | None]:
    """Valida credenciales. Regresa (ok, user_info | None)."""
    user = USERS.get(username.strip().lower())
    if not user:
        return False, None
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    if pw_hash == user["password_hash"]:
        return True, {**user, "username": username.strip().lower()}
    return False, None
