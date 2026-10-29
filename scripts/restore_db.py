"""Restore a verified SQLite backup after stopping the application."""
import argparse
import os
from contextlib import closing
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from backup_db import backup_database, database_path, integrity_ok

load_dotenv()


def restore_database(source: Path, destination: Path, backup_dir: Path) -> Path:
    source = source.resolve()
    destination = destination.resolve()
    backup_dir = backup_dir.resolve()
    if not integrity_ok(source):
        raise ValueError("Restore source is missing or failed SQLite integrity_check.")
    if source == destination:
        raise ValueError("Restore source must differ from the live database.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup_database(destination, backup_dir / f"assistant-pre-restore-{timestamp}.sqlite3")
    fd, temp_name = tempfile.mkstemp(prefix=".assistant-restore-", suffix=".tmp", dir=destination.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        with closing(sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True, timeout=30)) as src, closing(sqlite3.connect(temp, timeout=30)) as dst:
            src.backup(dst)
            if dst.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise sqlite3.DatabaseError("Restored database failed integrity_check.")
        os.chmod(temp, 0o600)
        os.replace(temp, destination)
        return destination
    finally:
        temp.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Path to a verified backup")
    parser.add_argument("--destination", type=Path, default=database_path())
    parser.add_argument("--backup-dir", type=Path, default=Path(os.getenv("BACKUP_DIR", "./backups")))
    parser.add_argument("--confirm", action="store_true", help="Required to replace the live database")
    args = parser.parse_args()
    if not args.confirm:
        parser.error("Restore is destructive; pass --confirm after stopping the application.")
    restored = restore_database(args.source, args.destination, args.backup_dir)
    print(f"Restore completed and integrity-checked: {restored}")


if __name__ == "__main__":
    main()
