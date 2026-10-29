"""Create a consistent, integrity-checked SQLite backup.

Run while the application is online; SQLite's backup API handles concurrent readers/writers.
"""
import argparse
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def database_path() -> Path:
    return Path(os.getenv("DATABASE_PATH", str(Path(os.getenv("DATA_DIR", "./data")) / "assistant.sqlite3"))).resolve()


def integrity_ok(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        with sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True, timeout=10) as connection:
            return connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    except sqlite3.Error:
        return False


def backup_database(source: Path, destination: Path) -> Path:
    source = source.resolve()
    destination = destination.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Database does not exist: {source}")
    if source == destination:
        raise ValueError("Backup destination must differ from the live database.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".assistant-backup-", suffix=".tmp", dir=destination.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        with sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True, timeout=30) as src, sqlite3.connect(temp, timeout=30) as dst:
            src.backup(dst)
            check = dst.execute("PRAGMA integrity_check").fetchone()[0]
            if check != "ok":
                raise sqlite3.DatabaseError("Backup integrity check failed.")
        os.chmod(temp, 0o600)
        os.replace(temp, destination)
        return destination
    finally:
        temp.unlink(missing_ok=True)


def prune_old_backups(directory: Path, keep_days: int = 14) -> int:
    cutoff = datetime.now(timezone.utc).timestamp() - keep_days * 86400
    removed = 0
    for path in directory.glob("assistant-*.sqlite3"):
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
                removed += 1
        except FileNotFoundError:
            pass
    return removed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=database_path())
    parser.add_argument("--backup-dir", type=Path, default=Path(os.getenv("BACKUP_DIR", "./backups")))
    parser.add_argument("--keep-days", type=int, default=int(os.getenv("BACKUP_RETENTION_DAYS", "14")))
    args = parser.parse_args()
    if args.keep_days < 1:
        parser.error("--keep-days must be at least 1")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = args.backup_dir / f"assistant-{timestamp}.sqlite3"
    backup_database(args.source, destination)
    prune_old_backups(args.backup_dir, args.keep_days)
    print(f"Backup created and integrity-checked: {destination.resolve()}")


if __name__ == "__main__":
    main()
