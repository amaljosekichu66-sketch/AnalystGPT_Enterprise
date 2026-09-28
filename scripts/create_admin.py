"""
Create an ADMIN account directly in the configured database.

Public self-registration cannot choose a role (every self-registered account
is an ANALYST), so the first administrator has to be created by someone with
shell access to the deployment - which is the trust boundary this script
relies on. Further role changes go through the admin user-management API.

Usage
-----
    python scripts/create_admin.py --username admin --email admin@example.com

The password is read from the ADMIN_BOOTSTRAP_PASSWORD environment variable
if set, otherwise prompted for without echo. It is never printed.

Inside Docker Compose:

    docker compose exec api python scripts/create_admin.py --username admin --email admin@example.com
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.api.dependencies.auth_dependencies import get_user_service  # noqa: E402
from src.identity.exceptions import UserAlreadyExistsError  # noqa: E402
from src.identity.models import UserCreate, UserRole  # noqa: E402
from src.identity.password_policy import WeakPasswordError, validate_password_strength  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create an AnalystGPT ADMIN account.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args(argv)

    password = os.getenv("ADMIN_BOOTSTRAP_PASSWORD") or getpass.getpass("Admin password: ")

    try:
        validate_password_strength(password, args.username, args.email)
    except WeakPasswordError as exc:
        print(f"Rejected: {exc}", file=sys.stderr)
        return 2

    try:
        user = get_user_service().register_user(
            UserCreate(
                username=args.username,
                email=args.email,
                password=password,
                role=UserRole.ADMIN,
            )
        )
    except UserAlreadyExistsError as exc:
        print(f"Not created: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Invalid input: {exc}", file=sys.stderr)
        return 2

    print(f"Created ADMIN '{user.username}' (id={user.id}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
