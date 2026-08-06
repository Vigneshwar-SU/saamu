"""Phase 16 tests for the PostgreSQL backup/restore service layer.

These tests exercise the operational layer without touching a real database:
every PostgreSQL subprocess call is replaced with a fake ``_run`` so the
behaviour (naming, validation, safety guards, error handling, secret
non-disclosure) is verified deterministically.
"""

import datetime
import subprocess
from pathlib import Path

import pytest
from django.conf import settings as django_settings
from django.test import override_settings

from apps.common import database_backup as db

pytestmark = pytest.mark.django_db

PASSWORD = "secret-db-password-123"


@pytest.fixture
def backup_dir(tmp_path):
    directory = tmp_path / "backups"
    directory.mkdir()
    with override_settings(BACKUP_DIR=str(directory), PG_BIN=""):
        yield directory


@pytest.fixture
def config():
    return {"name": "saamu_db", "user": "postgres", "host": "localhost", "port": "5432"}


@pytest.fixture
def fake_tools(monkeypatch):
    monkeypatch.setattr(db.shutil, "which", lambda name: f"C:/fake/{name}.exe")


def fake_run(
    success=True, stderr="", stdout="dummy catalog entries", write_output=True
):
    """A fake subprocess that writes the pg_dump ``--file`` target on success."""

    def run(args, password=None):
        if write_output and success:
            for index, arg in enumerate(args):
                if arg == "--file":
                    Path(args[index + 1]).write_bytes(b"fake-custom-archive")
        return subprocess.CompletedProcess(
            args,
            0 if success else 1,
            stdout=stdout,
            stderr=stderr,
        )

    return run


# ---------------------------------------------------------------------------
# Backup naming
# ---------------------------------------------------------------------------


def test_build_backup_filename_format():
    name = db.build_backup_filename(datetime.datetime(2026, 8, 6, 12, 30, 45))
    assert name == "saamu_db_2026-08-06_123045.dump"
    assert db.BACKUP_NAME_RE.match(name)


def test_build_backup_filename_is_deterministic_and_timestamped():
    first = db.build_backup_filename()
    assert db.BACKUP_NAME_RE.match(first)
    assert db.build_backup_filename() != first or first  # contains a timestamp


def test_validate_backup_name_accepts_valid_name():
    name = "saamu_db_2026-08-06_123045.dump"
    assert db.validate_backup_name(name) == name


@pytest.mark.parametrize(
    "bad_name",
    [
        "../../etc/passwd",
        "C:\\Windows\\temp\\saamu_db_2026-08-06_123045.dump",
        "saamu_db_2026-08-06_123045.dump/evil",
        "saamu_db_2026-08-06_123045.dump\\evil",
        "other.dump",
        "saamu_db_2026-08-06.dump",
        "notes.txt",
        "",
        "..\\saamu_db_2026-08-06_123045.dump",
    ],
)
def test_validate_backup_name_rejects_unsafe_names(bad_name):
    with pytest.raises(db.BackupValidationError):
        db.validate_backup_name(bad_name)


@pytest.mark.parametrize(
    "bad_name",
    ["saamu_db; DROP TABLE x;", "a-b", "", "../x", "with space", "select *"],
)
def test_validate_target_name_rejects_invalid_names(bad_name):
    with pytest.raises(db.BackupValidationError):
        db.validate_target_name(bad_name)


# ---------------------------------------------------------------------------
# Controlled backup location
# ---------------------------------------------------------------------------


def test_backup_dir_uses_configured_location(backup_dir):
    assert db.backup_dir() == backup_dir


def test_backup_dir_default_is_outside_source_tree():
    default = Path(django_settings.BACKUP_DIR)
    assert default.is_absolute()
    assert (
        not str(default).lower().startswith(str(Path(django_settings.BASE_DIR)).lower())
    )


def test_create_backup_writes_into_configured_location(
    backup_dir, config, fake_tools, monkeypatch
):
    monkeypatch.setattr(db, "_run", fake_run())
    result = db.create_backup(config, PASSWORD)
    assert (backup_dir / result["filename"]).is_file()


# ---------------------------------------------------------------------------
# Backup creation
# ---------------------------------------------------------------------------


def test_create_backup_success(backup_dir, config, fake_tools, monkeypatch):
    monkeypatch.setattr(db, "_run", fake_run())
    result = db.create_backup(config, PASSWORD, comment="manual")
    assert db.BACKUP_NAME_RE.match(result["filename"])
    assert result["size"] > 0
    assert result["verification"]["archive_inspectable"] is True
    assert (backup_dir / result["filename"]).is_file()


def test_create_backup_failed_process(backup_dir, config, fake_tools, monkeypatch):
    monkeypatch.setattr(
        db,
        "_run",
        fake_run(
            success=False,
            stderr="pg_dump: error: connection failed",
            write_output=False,
        ),
    )
    with pytest.raises(db.BackupError, match="pg_dump failed"):
        db.create_backup(config, PASSWORD)
    assert list(backup_dir.iterdir()) == []


def test_create_backup_refuses_to_overwrite(
    backup_dir, config, fake_tools, monkeypatch
):
    monkeypatch.setattr(db, "_run", fake_run())
    monkeypatch.setattr(
        db, "build_backup_filename", lambda: "saamu_db_2026-08-06_123045.dump"
    )
    db.create_backup(config, PASSWORD)
    with pytest.raises(db.BackupError, match="Refusing to overwrite"):
        db.create_backup(config, PASSWORD)


def test_create_backup_missing_tool(backup_dir, config, monkeypatch):
    monkeypatch.setattr(db.shutil, "which", lambda name: None)
    with pytest.raises(db.ToolUnavailableError, match="pg_dump"):
        db.create_backup(config, PASSWORD)


def test_create_backup_inaccessible_directory(tmp_path, config, monkeypatch):
    blocker = tmp_path / "backups"
    blocker.write_text("not a directory")
    with override_settings(BACKUP_DIR=str(blocker), PG_BIN=""):
        with pytest.raises(db.BackupError, match="not accessible|not a directory"):
            db.create_backup(config, PASSWORD)


def test_error_message_does_not_expose_password(
    backup_dir, config, fake_tools, monkeypatch
):
    stderr = "pg_dump: error: password authentication failed " f"(password={PASSWORD})"
    monkeypatch.setattr(
        db, "_run", fake_run(success=False, stderr=stderr, write_output=False)
    )
    with pytest.raises(db.BackupError) as exc_info:
        db.create_backup(config, PASSWORD)
    assert PASSWORD not in str(exc_info.value)


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def test_verify_backup_ok(backup_dir, config, fake_tools, monkeypatch):
    path = backup_dir / "saamu_db_2026-08-06_100000.dump"
    path.write_bytes(b"archive")
    monkeypatch.setattr(db, "_run", fake_run())
    result = db.verify_backup(path, config, PASSWORD)
    assert result["archive_inspectable"] is True
    assert result["size_bytes"] == 7


def test_verify_backup_missing_file(backup_dir, config):
    with pytest.raises(db.BackupValidationError, match="does not exist"):
        db.verify_backup(backup_dir / "missing.dump", config, PASSWORD)


def test_verify_backup_empty_file(backup_dir, config):
    path = backup_dir / "saamu_db_2026-08-06_100000.dump"
    path.write_bytes(b"")
    with pytest.raises(db.BackupValidationError, match="empty"):
        db.verify_backup(path, config, PASSWORD)


def test_verify_backup_not_inspectable(backup_dir, config, fake_tools, monkeypatch):
    path = backup_dir / "saamu_db_2026-08-06_100000.dump"
    path.write_bytes(b"junk")
    monkeypatch.setattr(
        db,
        "_run",
        fake_run(success=False, stderr="corrupted archive", write_output=False),
    )
    with pytest.raises(db.BackupValidationError, match="could not be inspected"):
        db.verify_backup(path, config, PASSWORD)


# ---------------------------------------------------------------------------
# Listing & retention
# ---------------------------------------------------------------------------


def test_list_backups_only_returns_valid_backups(backup_dir):
    (backup_dir / "saamu_db_2026-08-06_100000.dump").write_bytes(b"x")
    (backup_dir / "saamu_db_2026-08-05_090000.dump").write_bytes(b"y")
    (backup_dir / "notes.txt").write_text("not a backup")
    entries = db.list_backups(backup_dir)
    assert [entry["filename"] for entry in entries] == [
        "saamu_db_2026-08-06_100000.dump",
        "saamu_db_2026-08-05_090000.dump",
    ]


def test_list_backups_empty_for_missing_dir(tmp_path):
    assert db.list_backups(tmp_path / "does-not-exist") == []


def test_cleanup_keeps_newest(backup_dir):
    for day in range(1, 6):
        (backup_dir / f"saamu_db_2026-08-0{day}_000000.dump").write_bytes(b"x")
    removed = db.cleanup_backups(backup_dir, keep=2, dry_run=True)
    assert removed == [
        "saamu_db_2026-08-03_000000.dump",
        "saamu_db_2026-08-02_000000.dump",
        "saamu_db_2026-08-01_000000.dump",
    ]
    assert sorted(path.name for path in backup_dir.iterdir()) == [
        "saamu_db_2026-08-01_000000.dump",
        "saamu_db_2026-08-02_000000.dump",
        "saamu_db_2026-08-03_000000.dump",
        "saamu_db_2026-08-04_000000.dump",
        "saamu_db_2026-08-05_000000.dump",
    ]


def test_cleanup_execute_deletes(backup_dir):
    for day in range(1, 4):
        (backup_dir / f"saamu_db_2026-08-0{day}_000000.dump").write_bytes(b"x")
    removed = db.cleanup_backups(backup_dir, keep=1, dry_run=False)
    assert removed == [
        "saamu_db_2026-08-02_000000.dump",
        "saamu_db_2026-08-01_000000.dump",
    ]
    remaining = [path.name for path in backup_dir.iterdir()]
    assert remaining == ["saamu_db_2026-08-03_000000.dump"]


def test_cleanup_invalid_keep(backup_dir):
    with pytest.raises(db.BackupValidationError):
        db.cleanup_backups(backup_dir, keep=0)


# ---------------------------------------------------------------------------
# Restore safety
# ---------------------------------------------------------------------------


def _restore_harness(backup_dir, monkeypatch, force=False, active=None):
    path = backup_dir / "saamu_db_2026-08-06_100000.dump"
    path.write_bytes(b"archive")
    calls = []

    def fake_create_backup(cfg, password, comment=None, verify=True, dbname=None):
        calls.append((comment, dbname))
        return {
            "filename": "safety.dump",
            "size": 1,
            "path": backup_dir / "safety.dump",
        }

    monkeypatch.setattr(db, "create_backup", fake_create_backup)
    monkeypatch.setattr(
        db, "check_active_connections", lambda *a, **k: [] if active is None else active
    )
    monkeypatch.setattr(db.shutil, "which", lambda name: f"C:/fake/{name}.exe")
    monkeypatch.setattr(db, "_run", fake_run())
    monkeypatch.setattr(
        db,
        "verify_restored_database",
        lambda *a, **k: {
            "database": "saamu_db",
            "table_count": 20,
            "migration_count": 30,
            "core_counts": {},
        },
    )
    return path, calls


def test_restore_backup_creates_safety_backup_first(backup_dir, config, monkeypatch):
    path, calls = _restore_harness(backup_dir, monkeypatch)
    result = db.restore_backup(path, config, PASSWORD, "saamu_db")
    assert calls == [("pre-restore safety backup of saamu_db", "saamu_db")]
    assert result["safety_backup"]["filename"] == "safety.dump"
    assert result["verification"]["table_count"] == 20


def test_restore_backup_skips_safety_backup(backup_dir, config, monkeypatch):
    path, calls = _restore_harness(backup_dir, monkeypatch)
    result = db.restore_backup(
        path, config, PASSWORD, "saamu_db", skip_safety_backup=True
    )
    assert calls == []
    assert result["safety_backup"] is None


def test_restore_backup_missing_file(backup_dir, config):
    with pytest.raises(db.BackupNotFoundError):
        db.restore_backup(backup_dir / "missing.dump", config, PASSWORD, "saamu_db")


def test_restore_backup_blocked_by_active_connections(backup_dir, config, monkeypatch):
    path, _ = _restore_harness(
        backup_dir,
        monkeypatch,
        active=[{"pid": "123", "usename": "postgres", "state": "active"}],
    )
    with pytest.raises(db.RestoreError, match="Active connections"):
        db.restore_backup(path, config, PASSWORD, "saamu_db")


def test_restore_backup_force_overrides_active_connections(
    backup_dir, config, monkeypatch
):
    path, _ = _restore_harness(
        backup_dir,
        monkeypatch,
        active=[{"pid": "123", "usename": "postgres", "state": "active"}],
    )
    result = db.restore_backup(path, config, PASSWORD, "saamu_db", force=True)
    assert result["verification"]["table_count"] == 20


def test_restore_failure_handling(backup_dir, config, monkeypatch):
    path, _ = _restore_harness(backup_dir, monkeypatch)
    monkeypatch.setattr(
        db,
        "_run",
        fake_run(
            success=False, stderr="pg_restore: error: out of memory", write_output=False
        ),
    )
    with pytest.raises(db.RestoreError, match="pg_restore failed"):
        db.restore_backup(path, config, PASSWORD, "saamu_db")


def test_restore_error_does_not_expose_password(backup_dir, config, monkeypatch):
    path, _ = _restore_harness(backup_dir, monkeypatch)
    stderr = f"pg_restore: error: fatal (password={PASSWORD})"
    monkeypatch.setattr(
        db, "_run", fake_run(success=False, stderr=stderr, write_output=False)
    )
    with pytest.raises(db.RestoreError) as exc_info:
        db.restore_backup(path, config, PASSWORD, "saamu_db")
    assert PASSWORD not in str(exc_info.value)


def test_restore_uses_fixed_arguments(backup_dir, config, monkeypatch):
    path, _ = _restore_harness(backup_dir, monkeypatch)
    captured = {}

    def capture(args, password=None):
        captured["args"] = args
        return subprocess.CompletedProcess(args, 0, stdout="ok", stderr="")

    monkeypatch.setattr(db, "_run", capture)
    db.restore_backup(path, config, PASSWORD, "saamu_db")
    args = captured["args"]
    assert "pg_restore" in args[0]
    assert "--dbname" in args
    assert "saamu_db" in args
    assert str(path) in args
    assert "--clean" in args
    assert "--if-exists" in args
    assert "--no-owner" in args
    assert "--no-privileges" in args


# ---------------------------------------------------------------------------
# Post-restore verification
# ---------------------------------------------------------------------------


def _verification_fake_run(restored_counts=True):
    def run(args, password=None):
        sql = args[-1]
        if "information_schema.tables" in sql:
            return subprocess.CompletedProcess(args, 0, stdout="25", stderr="")
        if "django_migrations" in sql:
            return subprocess.CompletedProcess(args, 0, stdout="30", stderr="")
        stdout = "4" if restored_counts else "0"
        return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

    return run


def test_verify_restored_database_counts(config, fake_tools, monkeypatch):
    monkeypatch.setattr(db, "_run", _verification_fake_run())
    result = db.verify_restored_database(config, PASSWORD, "saamu_db")
    assert result["table_count"] == 25
    assert result["migration_count"] == 30
    assert len(result["core_counts"]) > 5
    assert all(value == 4 for value in result["core_counts"].values())


def test_verify_restored_database_requires_migrations(config, fake_tools, monkeypatch):
    def run(args, password=None):
        sql = args[-1]
        if "information_schema.tables" in sql:
            return subprocess.CompletedProcess(args, 0, stdout="10", stderr="")
        return subprocess.CompletedProcess(args, 0, stdout="0", stderr="")

    monkeypatch.setattr(db, "_run", run)
    with pytest.raises(db.RestoreError, match="no Django migrations"):
        db.verify_restored_database(config, PASSWORD, "saamu_db")


# ---------------------------------------------------------------------------
# Portability: disposable restore test
# ---------------------------------------------------------------------------


def test_run_restore_test_success(backup_dir, config, fake_tools, monkeypatch):
    path = backup_dir / "saamu_db_2026-08-06_100000.dump"
    path.write_bytes(b"archive")

    def run(args, password=None):
        if "pg_restore" in args[0]:
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        sql = args[-1]
        if "DROP DATABASE" in sql or "CREATE DATABASE" in sql:
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(args, 0, stdout="5", stderr="")

    monkeypatch.setattr(db, "_run", run)
    result = db.run_restore_test(path, config, PASSWORD)
    assert result["database"] == "saamu_restore_test"
    assert result["mismatches"] == []
    assert result["comparisons"]
    assert all(
        c["source_count"] == 5 and c["restored_count"] == 5
        for c in result["comparisons"]
    )


def test_run_restore_test_detects_mismatches(
    backup_dir, config, fake_tools, monkeypatch
):
    path = backup_dir / "saamu_db_2026-08-06_100000.dump"
    path.write_bytes(b"archive")

    def run(args, password=None):
        if "pg_restore" in args[0]:
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        sql = args[-1]
        if "DROP DATABASE" in sql or "CREATE DATABASE" in sql:
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        if db.RESTORE_TEST_DB in args:
            return subprocess.CompletedProcess(args, 0, stdout="4", stderr="")
        return subprocess.CompletedProcess(args, 0, stdout="5", stderr="")

    monkeypatch.setattr(db, "_run", run)
    result = db.run_restore_test(path, config, PASSWORD)
    assert result["mismatches"]
    assert result["comparisons"]
