from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()
# Verified against when the email is unknown, so "no such user" and "wrong password" take the same time.
DUMMY_HASH = _hasher.hash("not-a-real-password")


def hash_password(raw: str) -> str:
    return _hasher.hash(raw)


def verify_password(raw: str, stored: str) -> bool:
    try:
        return _hasher.verify(stored, raw)
    except (VerificationError, InvalidHashError):
        return False
