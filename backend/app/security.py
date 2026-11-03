"""Password handling.

For now passwords are stored in plain text (course requirement).
To add hashing later, change only these two functions (e.g. bcrypt / argon2)
and widen the `users.password` column.
"""

import secrets


def prepare_password(raw: str) -> str:
    return raw


def verify_password(raw: str, stored: str) -> bool:
    return secrets.compare_digest(raw.encode(), stored.encode())
