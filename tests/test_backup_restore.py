import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from backup_db import backup_database, integrity_ok
from restore_db import restore_database


def make_database(path: Path, value: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS sample (value TEXT NOT NULL)")
        connection.execute("DELETE FROM sample")
        connection.execute("INSERT INTO sample(value) VALUES(?)", (value,))


def read_value(path: Path) -> str:
    with sqlite3.connect(path) as connection:
        return connection.execute("SELECT value FROM sample").fetchone()[0]


def test_backup_is_consistent_and_integrity_checked(tmp_path):
    live = tmp_path / "data" / "assistant.sqlite3"
    backup = tmp_path / "backups" / "assistant-test.sqlite3"
    make_database(live, "before")
    assert backup_database(live, backup) == backup.resolve()
    assert integrity_ok(backup)
    assert read_value(backup) == "before"
    assert backup.stat().st_mode & 0o777 == 0o600


def test_restore_creates_pre_restore_backup_and_recovers_data(tmp_path):
    live = tmp_path / "data" / "assistant.sqlite3"
    backup = tmp_path / "backups" / "assistant-test.sqlite3"
    make_database(live, "original")
    backup_database(live, backup)
    make_database(live, "changed")

    restored = restore_database(backup, live, tmp_path / "backups")
    assert restored == live.resolve()
    assert integrity_ok(live)
    assert read_value(live) == "original"
    assert list((tmp_path / "backups").glob("assistant-pre-restore-*.sqlite3"))


def test_backup_refuses_to_overwrite_live_database(tmp_path):
    live = tmp_path / "assistant.sqlite3"
    make_database(live, "safe")
    with pytest.raises(ValueError):
        backup_database(live, live)


def test_restore_rejects_corrupt_database(tmp_path):
    corrupt = tmp_path / "corrupt.sqlite3"
    corrupt.write_bytes(b"not a sqlite database")
    live = tmp_path / "live.sqlite3"
    with pytest.raises(ValueError):
        restore_database(corrupt, live, tmp_path / "backups")
    assert not live.exists()
