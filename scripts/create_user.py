"""Create an account from a trusted shell without enabling public registration."""
import getpass
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import db, hash_password


def create_user(email: str, password: str) -> int:
    email = email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError("Enter a valid email address.")
    if len(password) < 12 or len(password) > 256:
        raise ValueError("Password must contain between 12 and 256 characters.")
    with db() as connection:
        if connection.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
            raise ValueError("An account with that email already exists.")
        cursor = connection.execute(
            "INSERT INTO users(email,password_hash,created_at) VALUES(?,?,datetime('now'))",
            (email, hash_password(password)),
        )
        return int(cursor.lastrowid)


def main():
    email = input("Account email: ").strip()
    password = getpass.getpass("Password (12+ characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    try:
        user_id = create_user(email, password)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Account created with ID {user_id}. Disable public registration unless it is intentionally required.")


if __name__ == "__main__":
    main()
