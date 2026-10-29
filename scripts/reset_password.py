"""Reset an account password from a trusted shell and revoke existing sessions."""
import getpass
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import db, hash_password


def reset_password(email: str, password: str) -> int:
    email = email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError("Enter a valid email address.")
    if len(password) < 12 or len(password) > 256:
        raise ValueError("Password must contain between 12 and 256 characters.")
    with db() as connection:
        user = connection.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if not user:
            raise ValueError("No account exists with that email.")
        user_id = int(user["id"])
        connection.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(password), user_id))
        connection.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
    return user_id


def main():
    email = input("Account email: ").strip()
    password = getpass.getpass("New password (12+ characters): ")
    confirmation = getpass.getpass("Confirm new password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    try:
        user_id = reset_password(email, password)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Password reset for account ID {user_id}; existing sessions have been revoked.")


if __name__ == "__main__":
    main()
