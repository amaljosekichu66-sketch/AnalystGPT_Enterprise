"""
Password acceptance policy for self-registration and admin bootstrap (SEC-08).

Follows the NIST SP 800-63B approach: a minimum length plus a check against
known-bad passwords, rather than composition rules. `aaaaaaaa` and `password`
used to be accepted.

Rules
-----
- at least `config.AUTH_PASSWORD_MIN_LENGTH` characters (default 8);
- not a commonly used / breached password (case-insensitive);
- at least 4 distinct characters (rejects `aaaaaaaa`, `abababab`);
- must not contain the username or the email's local part.
"""

from __future__ import annotations

from src.core import config

#: Frequently breached passwords, lower-cased. Deliberately short and local:
#: no network lookup happens at registration time.
# fmt: off
COMMON_PASSWORDS: frozenset[str] = frozenset(
    {
        "password", "password1", "password12", "password123", "password1234", "passw0rd", "p@ssw0rd",
        "p@ssword", "passwort", "123456789", "1234567890", "12345678", "123123123", "11111111",
        "00000000", "87654321", "qwerty123", "qwertyuiop", "qwerty12", "1q2w3e4r", "1qaz2wsx",
        "zaq12wsx", "asdfghjkl", "asdf1234", "iloveyou", "iloveyou1", "admin123", "admin1234",
        "administrator", "welcome1", "welcome123", "letmein1", "letmein123", "changeme", "changeme1",
        "sunshine", "princess", "football", "baseball", "superman", "trustno1", "abc12345",
        "abcd1234", "monkey123", "dragon123", "master123", "secret123", "default1", "test1234",
        "testtest", "guest123", "login123", "starwars", "whatever", "computer", "internet",
        "analystgpt", "analystgpt1", "analystgpt123",
    }
)
# fmt: on

_MIN_DISTINCT_CHARACTERS = 4


class WeakPasswordError(ValueError):
    """Raised when a password fails the acceptance policy."""


def validate_password_strength(password: str, username: str | None = None, email: str | None = None) -> None:
    """Raise `WeakPasswordError` with a user-facing reason if `password` is not acceptable."""
    minimum = int(config.AUTH_PASSWORD_MIN_LENGTH)
    if len(password) < minimum:
        raise WeakPasswordError(f"Password must be at least {minimum} characters long.")

    lowered = password.lower()
    if lowered in COMMON_PASSWORDS:
        raise WeakPasswordError("Password is too common. Choose a less predictable password.")

    if len(set(password)) < _MIN_DISTINCT_CHARACTERS:
        raise WeakPasswordError("Password is too repetitive. Use more varied characters.")

    for identity in (username, (email or "").split("@")[0]):
        if identity and len(identity) >= 3 and identity.lower() in lowered:
            raise WeakPasswordError("Password must not contain your username or email address.")
