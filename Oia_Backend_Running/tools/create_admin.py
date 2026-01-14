#!/usr/bin/env python3
"""
Create an admin user using the project's DatabaseOperations helper.

Run from the repository root:
  python backend/tools/create_admin.py --username oia_admin --password 'YourP@ssw0rd'

If you omit --password the script will generate a secure random password and print it.
"""
from pathlib import Path
import sys
import asyncio
import argparse
import secrets

# Ensure repo root is on sys.path so we can import backend package regardless of cwd
THIS = Path(__file__).resolve()
REPO_ROOT = THIS.parents[2]
sys.path.insert(0, str(REPO_ROOT))

try:
    from backend.database import DatabaseOperations
except Exception as exc:
    print("Failed to import backend.database. Make sure you're running this from the repo (or that backend/ exists).")
    print("Error:", exc)
    sys.exit(1)


async def _create_admin(username: str, password: str):
    created = await DatabaseOperations.create_admin(username, password)
    return created


def generate_password(length: int = 16) -> str:
    # URL-safe token is good; include a few extra chars for punctuation if required
    return secrets.token_urlsafe(length)[:length]


def main():
    parser = argparse.ArgumentParser(description="Create an admin user in the OIA backend database")
    parser.add_argument("--username", required=True, help="Admin username to create")
    parser.add_argument("--password", required=False, help="Plain-text password. If omitted a secure one will be generated.")
    args = parser.parse_args()

    username = args.username
    password = args.password or generate_password(16)

    print(f"Creating admin user '{username}'...")

    try:
        created = asyncio.run(_create_admin(username, password))
    except Exception as e:
        print("Failed to create admin:", e)
        sys.exit(1)

    print("Admin created successfully:")
    print("  username:", created.get('username'))
    print("  id:", created.get('id'))
    print("  NOTE: the password is shown only now — store it securely!")
    print("  password:", password)
    print("\nRecommendation: store this password in your password manager and rotate the default seeded admin in production.")


if __name__ == '__main__':
    main()
