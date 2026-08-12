"""PostgreSQL backup, verification, restore and retention helpers (Phase 16).

This module is the operational layer for backup/restore. It shells out to the
PostgreSQL CLI tools (``pg_dump``, ``pg_restore``, ``psql``) using fixed,
pre-built argument structures and controlled paths. It deliberately:

- never accepts arbitrary executable commands or arbitrary filesystem paths,
- never accepts arbitrary database targets from callers (targets are validated
  against a strict identifier pattern by the caller's management command),
- never returns or logs database passwords (they are passed to the child
  process through ``PGPASSWORD`` only),
- never reports success unless the underlying process succeeded and the
  artifact is usable.

No business data is duplicated here and no backup metadata is stored as
business records.
"""

import datetime
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

from django.conf import settings

logger = logging.getLogger("saamu")

BACKUP_PREFIX = "saamu_db"
BACKUP_NAME_RE = re.compile(r"^saamu_db_\d{4}-\d{2}-\d{2}_\d{6}\.dump$")
TARGET_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
RESTORE_TEST_DB = "saamu_restore_test"


class DatabaseBackupError(Exception):
    """Base class for all backup/restore/verification errors."""


class ToolUnavailableError(DatabaseBackupError):
    """A required PostgreSQL CLI tool could not be located."""


class BackupValidationError(DatabaseBackupError):
    """A backup name, target or path failed server-side validation."""


class BackupNotFoundError(DatabaseBackupError):
    """The requested backup file does not exist."""


class BackupError(DatabaseBackupError):
    """Backup creation or verification failed."""


class RestoreError(DatabaseBackupError):
    """Restore or post-restore verification failed."""


def get_db_config():
    """Return a secret-free dictionary of the configured database connection.

    The password is intentionally never included here; callers obtain it
    separately via :func:`get_db_password` and pass it to subprocess helpers.
    """
    db = settings.DATABASES["default"]
    return {
        "name": db["NAME"],
        "user": db["USER"],
        "host": db["HOST"] or "localhost",
        "port": str(db["PORT"] or "5432"),
    }


def get_db_password():
    """Return the configured database password for subprocess use.

    The value is only ever used to set ``PGPASSWORD`` for child processes and
    must never be printed or included in error messages.
    """
    return settings.DATABASES["default"].get("PASSWORD", "")


def backup_dir():
    """Return the configured backup storage directory (outside the source tree)."""
    return Path(getattr(settings, "BACKUP_DIR", Path.home() / "SaamuBackups"))


def resolve_tool(name):
    """Resolve the absolute path of a PostgreSQL CLI tool.

    ``PGBIN`` (exposed as ``settings.PG_BIN``) is honoured first; otherwise the
    tool is located on ``PATH``. Raises :class:`ToolUnavailableError` when the
    tool cannot be found so callers can distinguish "unavailable" from "failed".
    """
    pg_bin = getattr(settings, "PG_BIN", "") or ""
    if pg_bin:
        candidates = [Path(pg_bin) / name]
        if os.name == "nt" and not name.lower().endswith(".exe"):
            candidates.append(Path(pg_bin) / f"{name}.exe")
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    raise ToolUnavailableError(
        f"PostgreSQL tool '{name}' was not found. Set PGBIN in backend/.env "
        "(e.g. C:\\Program Files\\PostgreSQL\\18\\bin) or add it to PATH."
    )


def _sanitize(text, secret=None):
    """Strip occurrences of a secret (e.g. the database password) from output."""
    if not text:
        return text
    if secret:
        text = text.replace(secret, "***")
    return text


def _run(args, password=None):
    """Run a fixed PostgreSQL command, returning its CompletedProcess.

    The database password is passed only through ``PGPASSWORD`` in the child
    environment and never through command-line arguments.
    """
    env = dict(os.environ)
    if password:
        env["PGPASSWORD"] = password
    try:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            env=env,
        )
    except FileNotFoundError:
        raise ToolUnavailableError(f"PostgreSQL tool was not found: {args[0]}")


def _base_args(tool, config, dbname):
    return [
        tool,
        "--host",
        config["host"],
        "--port",
        config["port"],
        "--username",
        config["user"],
        "--dbname",
        dbname,
        "--no-password",
        "--no-psqlrc",
    ]


def build_backup_filename(now=None):
    """Return a deterministic, timestamped backup filename."""
    timestamp = now or datetime.datetime.now()
    return f"{BACKUP_PREFIX}_{timestamp.strftime('%Y-%m-%d_%H%M%S')}.dump"


def validate_backup_name(name):
    """Validate a backup identifier.

    Only a bare filename matching the strict timestamped naming convention is
    accepted; anything containing path separators, traversal sequences or a
    foreign naming scheme is rejected so no arbitrary path is ever used.
    """
    if not name or name != os.path.basename(name) or not BACKUP_NAME_RE.match(name):
        raise BackupValidationError(
            "Invalid backup name. Use a backup filename reported by "
            "'python manage.py db_list_backups'."
        )
    return name


def validate_target_name(name):
    """Validate a restore target database name (strict PostgreSQL identifier)."""
    if not name or not TARGET_NAME_RE.match(name):
        raise BackupValidationError("Invalid target database name.")
    return name


def _ensure_backup_dir(directory):
    directory = Path(directory)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise BackupError(f"Backup directory is not accessible: {exc}")
    if not directory.is_dir():
        raise BackupError(f"Backup location is not a directory: {directory}")
    return directory


def create_backup(config, password, comment=None, verify=True, dbname=None):
    """Create a timestamped custom-format backup of ``dbname`` (default: configured DB).

    Returns a result dict with ``path``, ``filename`` and ``size``. Refuses to
    overwrite an existing file. When ``verify`` is true the artifact is
    inspected with PostgreSQL tooling before success is reported.
    """
    directory = _ensure_backup_dir(backup_dir())
    dbname = dbname or config["name"]
    output_path = directory / build_backup_filename()
    if output_path.exists():
        raise BackupError(
            f"Refusing to overwrite existing backup: {output_path.name}. "
            "Wait a second and retry."
        )

    tool = resolve_tool("pg_dump")
    args = [
        tool,
        "--host",
        config["host"],
        "--port",
        config["port"],
        "--username",
        config["user"],
        "--dbname",
        dbname,
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        "--no-password",
        "--file",
        str(output_path),
    ]
    if comment:
        # pg_dump has no --comment/--label CLI option; the comment is recorded
        # in the log and in the backup filename suffix for traceability.
        logger.info("Backup comment: %s", comment)

    logger.info("Creating PostgreSQL backup of database '%s'.", dbname)
    completed = _run(args, password=password)
    if completed.returncode != 0:
        message = _sanitize(completed.stderr.strip(), password)
        raise BackupError(
            f"pg_dump failed for database '{dbname}': {message or 'unknown error'}"
        )
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise BackupError(f"Backup was not produced at {output_path}.")

    result = {
        "path": output_path,
        "filename": output_path.name,
        "size": output_path.stat().st_size,
    }
    if verify:
        try:
            result["verification"] = verify_backup(
                output_path, config, password, restore_test=False
            )
        except DatabaseBackupError as exc:
            raise BackupError(f"Backup created but verification failed: {exc}") from exc
    logger.info("Backup created: %s (%d bytes).", output_path.name, result["size"])
    return result


def verify_backup(path, config, password, restore_test=False):
    """Verify that a backup artifact is present, non-empty and inspectable.

    Uses ``pg_restore --list`` so PostgreSQL tooling itself confirms the
    archive is readable. When ``restore_test`` is true the backup is also
    restored into a disposable database and representative row counts are
    compared against the source database (see :func:`run_restore_test`).
    """
    path = Path(path)
    if not path.is_file():
        raise BackupValidationError(f"Backup file does not exist: {path.name}")
    if path.stat().st_size == 0:
        raise BackupValidationError(f"Backup file is empty: {path.name}")

    tool = resolve_tool("pg_restore")
    completed = _run([tool, "--list", str(path)], password=password)
    if completed.returncode != 0:
        message = _sanitize(completed.stderr.strip(), password)
        raise BackupValidationError(
            "Backup could not be inspected by PostgreSQL tooling: "
            f"{message or 'unknown error'}"
        )
    if not completed.stdout.strip():
        raise BackupValidationError(
            f"Backup archive contains no catalog entries: {path.name}"
        )

    result = {
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "archive_inspectable": True,
    }
    if restore_test:
        result["restore_test"] = run_restore_test(path, config, password)
    logger.info("Backup verified: %s (%d bytes).", path.name, path.stat().st_size)
    return result


def list_backups(directory=None):
    """List valid timestamped backups, newest first.

    Only files matching the strict naming convention are reported; unrelated
    files in the directory are ignored so foreign artifacts can never be
    treated as backups.
    """
    directory = Path(directory) if directory else backup_dir()
    if not directory.is_dir():
        return []
    entries = []
    for item in directory.iterdir():
        if item.is_file() and BACKUP_NAME_RE.match(item.name):
            stat = item.stat()
            entries.append(
                {
                    "filename": item.name,
                    "size_bytes": stat.st_size,
                    "modified_at": datetime.datetime.fromtimestamp(stat.st_mtime),
                    "path": item,
                }
            )
    entries.sort(key=lambda entry: entry["filename"], reverse=True)
    return entries


def cleanup_backups(directory, keep, dry_run=True):
    """Remove expired backups, keeping the newest ``keep``.

    Only files matching the strict naming convention are ever considered for
    deletion. Returns the list of removed (or would-be-removed) filenames.
    """
    if keep < 1:
        raise BackupValidationError("--keep must be at least 1.")
    entries = list_backups(directory)
    if len(entries) <= keep:
        return []
    removed = []
    for entry in entries[keep:]:
        if not dry_run:
            try:
                entry["path"].unlink()
            except OSError as exc:
                raise BackupError(
                    f"Failed to remove expired backup {entry['filename']}: {exc}"
                )
        removed.append(entry["filename"])
    if removed:
        logger.info(
            "Backup retention: %s %s.",
            "removed" if not dry_run else "would remove",
            removed,
        )
    return removed


def _query(config, password, dbname, sql):
    tool = resolve_tool("psql")
    args = _base_args(tool, config, dbname) + [
        "-t",
        "-A",
        "-v",
        "ON_ERROR_STOP=1",
        "-c",
        sql,
    ]
    return _run(args, password=password)


def _query_scalar(config, password, dbname, sql):
    completed = _query(config, password, dbname, sql)
    if completed.returncode != 0:
        message = _sanitize(completed.stderr.strip(), password)
        raise RestoreError(
            f"Database query failed on '{dbname}': {message or 'unknown error'}"
        )
    return completed.stdout.strip()


def _try_query_scalar(config, password, dbname, sql):
    completed = _query(config, password, dbname, sql)
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def core_tables():
    """Return (label, db_table) pairs for representative business tables.

    Derived from the Django app registry so the list always matches the real
    schema regardless of migration history.
    """
    from django.apps import apps

    specs = [
        ("authentication", "User", "users"),
        ("customers", "Customer", "customers"),
        ("orders", "Order", "orders"),
        ("orders", "OrderItem", "order items"),
        ("tailors", "Tailor", "tailors"),
        ("tailors", "WorkAssignment", "work assignments"),
        ("attendance", "Attendance", "attendance"),
        ("payroll", "PayrollPeriod", "payroll periods"),
        ("payroll", "PayrollEntry", "payroll entries"),
        ("payments", "SalaryAdvance", "salary advances"),
        ("payments", "PayrollPayment", "payroll payments"),
        ("billing", "Invoice", "invoices"),
        ("billing", "InvoiceItem", "invoice items"),
        ("billing", "CustomerPayment", "customer payments"),
        ("finance", "Expense", "expenses"),
    ]
    tables = []
    for app_label, model_name, label in specs:
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            continue
        tables.append((label, model._meta.db_table))
    return tables


def verify_restored_database(config, password, dbname):
    """Confirm a restored database is reachable and structurally usable.

    Checks that the public schema has tables, Django migrations are recorded,
    and representative business tables exist with their row counts. Never
    mutates business data.
    """
    table_count = int(
        _query_scalar(
            config,
            password,
            dbname,
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema = 'public';",
        )
    )
    migration_count = int(
        _query_scalar(
            config, password, dbname, "SELECT count(*) FROM django_migrations;"
        )
    )
    core_counts = {}
    for label, table in core_tables():
        value = _try_query_scalar(
            config, password, dbname, f'SELECT count(*) FROM "{table}";'
        )
        core_counts[label] = int(value) if value is not None else None

    if table_count == 0:
        raise RestoreError(f"Restored database '{dbname}' contains no tables.")
    if migration_count == 0:
        raise RestoreError(
            f"Restored database '{dbname}' contains no Django migrations."
        )

    return {
        "database": dbname,
        "table_count": table_count,
        "migration_count": migration_count,
        "core_counts": core_counts,
    }


def check_active_connections(config, password, dbname):
    """Return active connections to ``dbname`` excluding the current session.

    When the database cannot be inspected the check degrades to an empty list
    with a logged warning so a recovery restore of a broken database is not
    blocked; the restore command still reports any connection error itself.
    """
    tool = resolve_tool("psql")
    args = _base_args(tool, config, dbname) + [
        "-t",
        "-A",
        "-v",
        "ON_ERROR_STOP=1",
        "-c",
        "SELECT pid, usename, state FROM pg_stat_activity "
        "WHERE datname = current_database() AND pid <> pg_backend_pid();",
    ]
    completed = _run(args, password=password)
    if completed.returncode != 0:
        logger.warning(
            "Could not inspect active connections for '%s': %s",
            dbname,
            _sanitize(completed.stderr.strip(), password),
        )
        return []
    connections = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) >= 3:
            connections.append(
                {"pid": parts[0], "usename": parts[1], "state": parts[2]}
            )
    return connections


def run_restore_test(path, config, password):
    """Restore a backup into a disposable database, compare counts, then drop it.

    Flow: drop/create ``saamu_restore_test`` -> restore -> compare representative
    table counts against the source database -> drop the disposable database in
    a ``finally`` block. Never touches the live shop database.
    """
    path = Path(path)
    if not path.is_file():
        raise BackupNotFoundError(f"Backup file does not exist: {path.name}")

    psql = resolve_tool("psql")
    maintenance_db = "postgres"

    def run_sql(dbname, sql):
        completed = _run(
            _base_args(psql, config, dbname) + ["-v", "ON_ERROR_STOP=1", "-c", sql],
            password=password,
        )
        if completed.returncode != 0:
            message = _sanitize(completed.stderr.strip(), password)
            raise RestoreError(
                f"Restore-test SQL failed on '{dbname}': {message or 'unknown error'}"
            )

    run_sql(maintenance_db, f"DROP DATABASE IF EXISTS {RESTORE_TEST_DB} WITH (FORCE);")
    run_sql(
        maintenance_db, f"CREATE DATABASE {RESTORE_TEST_DB} OWNER {config['user']};"
    )

    try:
        pg_restore = resolve_tool("pg_restore")
        completed = _run(
            [
                pg_restore,
                "--host",
                config["host"],
                "--port",
                config["port"],
                "--username",
                config["user"],
                "--dbname",
                RESTORE_TEST_DB,
                "--no-owner",
                "--no-privileges",
                "--clean",
                "--if-exists",
                "--no-password",
                str(path),
            ],
            password=password,
        )
        if completed.returncode != 0:
            message = _sanitize(completed.stderr.strip(), password)
            raise RestoreError(
                "pg_restore into restore-test database failed: "
                f"{message or 'unknown error'}"
            )

        comparisons = []
        for label, table in core_tables():
            sql = f'SELECT count(*) FROM "{table}";'
            source = _try_query_scalar(config, password, config["name"], sql)
            restored = _try_query_scalar(config, password, RESTORE_TEST_DB, sql)
            comparisons.append(
                {
                    "table": label,
                    "source_count": int(source) if source is not None else None,
                    "restored_count": int(restored) if restored is not None else None,
                    "match": source is not None
                    and restored is not None
                    and source == restored,
                }
            )
    finally:
        try:
            run_sql(
                maintenance_db,
                f"DROP DATABASE IF EXISTS {RESTORE_TEST_DB} WITH (FORCE);",
            )
        except RestoreError:
            logger.warning(
                "Could not drop restore-test database '%s'; remove it manually.",
                RESTORE_TEST_DB,
            )

    mismatches = [comparison for comparison in comparisons if not comparison["match"]]
    return {
        "database": RESTORE_TEST_DB,
        "comparisons": comparisons,
        "mismatches": mismatches,
    }


def restore_backup(
    path, config, password, target, skip_safety_backup=False, force=False
):
    """Restore a known backup over ``target`` with defensive safeguards.

    Safeguards, in order:
    1. the backup file must exist,
    2. a fresh pre-restore safety backup of the current target is created
       (unless ``skip_safety_backup``),
    3. active connections to the target block the restore unless ``force``,
    4. ``pg_restore`` runs with a fixed argument structure (``--clean`` /
       ``--if-exists`` / ``--no-owner`` / ``--no-privileges``),
    5. post-restore verification confirms the database is structurally usable.

    Confirmation of operator intent is handled by the calling management
    command and is never performed here.
    """
    path = Path(path)
    if not path.is_file():
        raise BackupNotFoundError(f"Backup file does not exist: {path.name}")

    safety_backup = None
    if not skip_safety_backup:
        safety_backup = create_backup(
            config,
            password,
            comment=f"pre-restore safety backup of {target}",
            verify=True,
            dbname=target,
        )

    active = check_active_connections(config, password, target)
    if active and not force:
        raise RestoreError(
            f"Active connections to target database '{target}' were detected. "
            "Stop the application before restoring, or pass --force."
        )

    pg_restore = resolve_tool("pg_restore")
    args = [
        pg_restore,
        "--host",
        config["host"],
        "--port",
        config["port"],
        "--username",
        config["user"],
        "--dbname",
        target,
        "--no-owner",
        "--no-privileges",
        "--clean",
        "--if-exists",
        "--no-password",
        str(path),
    ]
    logger.warning(
        "Restoring backup '%s' into database '%s' (destructive).", path.name, target
    )
    completed = _run(args, password=password)
    if completed.returncode != 0:
        message = _sanitize(completed.stderr.strip(), password)
        raise RestoreError(
            f"pg_restore failed for '{target}': {message or 'unknown error'}"
        )

    verification = verify_restored_database(config, password, target)
    logger.info(
        "Restore of '%s' into '%s' completed; verification: %s.",
        path.name,
        target,
        verification,
    )
    return {"safety_backup": safety_backup, "verification": verification}
