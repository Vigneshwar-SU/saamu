"""Phase 16 tests for the backup/restore management commands.

The service functions are monkeypatched so the commands' operator-facing
behaviour (output, confirmation requirements, validation, error reporting)
is verified without touching a real database.
"""

import io
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from apps.common import database_backup as db

pytestmark = pytest.mark.django_db


@pytest.fixture
def backup_dir(tmp_path):
    directory = tmp_path / "backups"
    directory.mkdir()
    with override_settings(BACKUP_DIR=str(directory), PG_BIN=""):
        yield directory


@pytest.fixture
def db_config(monkeypatch):
    monkeypatch.setattr(
        db,
        "get_db_config",
        lambda: {
            "name": "saamu_db",
            "user": "postgres",
            "host": "localhost",
            "port": "5432",
        },
    )
    monkeypatch.setattr(db, "get_db_password", lambda: "secret-db-password")


def _make_backup(backup_dir, name="saamu_db_2026-08-06_100000.dump"):
    path = Path(backup_dir) / name
    path.write_bytes(b"archive")
    return path


# ---------------------------------------------------------------------------
# db_backup
# ---------------------------------------------------------------------------


def test_db_backup_success(backup_dir, db_config, monkeypatch):
    monkeypatch.setattr(
        db,
        "create_backup",
        lambda *a, **k: {
            "filename": "saamu_db_2026-08-06_100000.dump",
            "size": 123,
            "verification": {"archive_inspectable": True, "size_bytes": 123},
        },
    )
    out = io.StringIO()
    call_command("db_backup", stdout=out)
    value = out.getvalue()
    assert "Backup created: saamu_db_2026-08-06_100000.dump" in value
    assert "Verification: archive inspectable" in value


def test_db_backup_failure_raises(backup_dir, db_config, monkeypatch):
    def fail(*a, **k):
        raise db.BackupError("pg_dump failed")

    monkeypatch.setattr(db, "create_backup", fail)
    with pytest.raises(CommandError, match="pg_dump failed"):
        call_command("db_backup")


def test_db_backup_missing_tool_raises(backup_dir, db_config, monkeypatch):
    def fail(*a, **k):
        raise db.ToolUnavailableError("PostgreSQL tool 'pg_dump' was not found.")

    monkeypatch.setattr(db, "create_backup", fail)
    with pytest.raises(CommandError, match="pg_dump"):
        call_command("db_backup")


# ---------------------------------------------------------------------------
# db_list_backups
# ---------------------------------------------------------------------------


def test_db_list_backups(backup_dir):
    _make_backup(backup_dir)
    out = io.StringIO()
    call_command("db_list_backups", stdout=out)
    value = out.getvalue()
    assert "saamu_db_2026-08-06_100000.dump" in value


def test_db_list_backups_empty(backup_dir):
    out = io.StringIO()
    call_command("db_list_backups", stdout=out)
    assert "No backups found." in out.getvalue()


# ---------------------------------------------------------------------------
# db_verify
# ---------------------------------------------------------------------------


def test_db_verify_newest_default(backup_dir, monkeypatch):
    older = _make_backup(backup_dir, "saamu_db_2026-08-05_000000.dump")
    newer = _make_backup(backup_dir, "saamu_db_2026-08-06_000000.dump")
    seen = {}

    def verify(path, config, password, restore_test=False):
        seen["path"] = path
        return {"filename": path.name, "size_bytes": 1, "archive_inspectable": True}

    monkeypatch.setattr(db, "verify_backup", verify)
    out = io.StringIO()
    call_command("db_verify", stdout=out)
    assert seen["path"] == newer
    assert "Backup verified: saamu_db_2026-08-06_000000.dump" in out.getvalue()


def test_db_verify_specific_backup(backup_dir, monkeypatch):
    _make_backup(backup_dir, "saamu_db_2026-08-05_000000.dump")
    seen = {}

    def verify(path, config, password, restore_test=False):
        seen["path"] = path
        return {"filename": path.name, "size_bytes": 1, "archive_inspectable": True}

    monkeypatch.setattr(db, "verify_backup", verify)
    call_command("db_verify", "--backup", "saamu_db_2026-08-05_000000.dump")
    assert seen["path"].name == "saamu_db_2026-08-05_000000.dump"


def test_db_verify_restore_test_ok(backup_dir, monkeypatch):
    _make_backup(backup_dir)
    monkeypatch.setattr(
        db,
        "verify_backup",
        lambda path, config, password, restore_test=False: {
            "filename": path.name,
            "size_bytes": 1,
            "archive_inspectable": True,
            "restore_test": {
                "database": "saamu_restore_test",
                "comparisons": [{"table": "customers", "match": True}],
                "mismatches": [],
            },
        },
    )
    out = io.StringIO()
    call_command("db_verify", "--restore-test", stdout=out)
    assert "0 mismatches" in out.getvalue()


def test_db_verify_restore_test_mismatch_fails(backup_dir, monkeypatch):
    _make_backup(backup_dir)
    monkeypatch.setattr(
        db,
        "verify_backup",
        lambda path, config, password, restore_test=False: {
            "filename": path.name,
            "size_bytes": 1,
            "archive_inspectable": True,
            "restore_test": {
                "database": "saamu_restore_test",
                "comparisons": [{"table": "customers", "match": False}],
                "mismatches": [{"table": "customers"}],
            },
        },
    )
    with pytest.raises(CommandError, match="count mismatches"):
        call_command("db_verify", "--restore-test")


def test_db_verify_no_backups(backup_dir, monkeypatch):
    monkeypatch.setattr(db, "list_backups", lambda *a, **k: [])
    with pytest.raises(CommandError, match="No backups found"):
        call_command("db_verify")


def test_db_verify_unknown_backup(backup_dir, monkeypatch):
    _make_backup(backup_dir)
    with pytest.raises(CommandError, match="Backup not found"):
        call_command("db_verify", "--backup", "saamu_db_2026-08-04_000000.dump")


# ---------------------------------------------------------------------------
# db_restore
# ---------------------------------------------------------------------------


def test_db_restore_requires_confirmation(backup_dir, db_config, monkeypatch):
    _make_backup(backup_dir)
    monkeypatch.setattr(
        db,
        "restore_backup",
        lambda *a, **k: {"safety_backup": None, "verification": {}},
    )
    with pytest.raises(CommandError, match="explicit confirmation"):
        call_command("db_restore", "--backup", "saamu_db_2026-08-06_100000.dump")


def test_db_restore_with_yes_proceeds(backup_dir, db_config, monkeypatch):
    _make_backup(backup_dir)
    captured = {}

    def fake_restore(
        path, config, password, target, skip_safety_backup=False, force=False
    ):
        captured["target"] = target
        return {
            "safety_backup": {"filename": "safety.dump", "size": 1},
            "verification": {
                "table_count": 20,
                "migration_count": 30,
                "core_counts": {"customers": 5},
            },
        }

    monkeypatch.setattr(db, "restore_backup", fake_restore)
    out = io.StringIO()
    call_command(
        "db_restore",
        "--backup",
        "saamu_db_2026-08-06_100000.dump",
        "--yes",
        stdout=out,
    )
    assert captured["target"] == "saamu_db"
    value = out.getvalue()
    assert (
        "Restore of saamu_db_2026-08-06_100000.dump into saamu_db completed." in value
    )
    assert "Pre-restore safety backup: safety.dump" in value


def test_db_restore_rejects_invalid_backup(backup_dir, db_config):
    with pytest.raises(CommandError, match="Invalid backup name"):
        call_command("db_restore", "--backup", "../../evil.dump", "--yes")


def test_db_restore_backup_not_found(backup_dir, db_config):
    with pytest.raises(CommandError, match="Backup not found"):
        call_command(
            "db_restore", "--backup", "saamu_db_2026-08-06_100000.dump", "--yes"
        )


def test_db_restore_rejects_invalid_target(backup_dir, db_config, monkeypatch):
    _make_backup(backup_dir)
    monkeypatch.setattr(
        db,
        "restore_backup",
        lambda *a, **k: {"safety_backup": None, "verification": {}},
    )
    with pytest.raises(CommandError, match="Invalid target database name"):
        call_command(
            "db_restore",
            "--backup",
            "saamu_db_2026-08-06_100000.dump",
            "--target",
            "bad-name; DROP TABLE users;",
            "--yes",
        )


def test_db_restore_failure_handling(backup_dir, db_config, monkeypatch):
    _make_backup(backup_dir)

    def fail(*a, **k):
        raise db.RestoreError("pg_restore failed")

    monkeypatch.setattr(db, "restore_backup", fail)
    with pytest.raises(CommandError, match="pg_restore failed"):
        call_command(
            "db_restore", "--backup", "saamu_db_2026-08-06_100000.dump", "--yes"
        )


# ---------------------------------------------------------------------------
# db_cleanup
# ---------------------------------------------------------------------------


def test_db_cleanup_dry_run(backup_dir):
    for day in range(1, 4):
        _make_backup(backup_dir, f"saamu_db_2026-08-0{day}_000000.dump")
    out = io.StringIO()
    call_command("db_cleanup", "--keep", "1", stdout=out)
    assert "would remove" in out.getvalue()
    assert len(list(Path(backup_dir).iterdir())) == 3


def test_db_cleanup_execute(backup_dir):
    for day in range(1, 4):
        _make_backup(backup_dir, f"saamu_db_2026-08-0{day}_000000.dump")
    out = io.StringIO()
    call_command("db_cleanup", "--keep", "1", "--execute", stdout=out)
    assert "removed:" in out.getvalue()
    remaining = [path.name for path in Path(backup_dir).iterdir()]
    assert remaining == ["saamu_db_2026-08-03_000000.dump"]


def test_db_cleanup_invalid_keep(backup_dir):
    with pytest.raises(CommandError, match="--keep"):
        call_command("db_cleanup", "--keep", "0")
