"""Restore a known backup over a target database (destructive, guarded).

This is an explicit operator procedure, not an ordinary application mutation.
The command refuses to run without explicit confirmation, creates a fresh
pre-restore safety backup of the current target by default, blocks the restore
while the target has active connections (unless ``--force``), and verifies the
database after the restore.
"""

import sys

from django.core.management.base import BaseCommand, CommandError

from apps.common import database_backup as db


class Command(BaseCommand):
    help = (
        "Restore a known backup over a database (destructive). Requires "
        "explicit confirmation; a pre-restore safety backup is created first."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--backup",
            required=True,
            help="Backup filename to restore (must be listed by db_list_backups).",
        )
        parser.add_argument(
            "--target",
            default=None,
            help="Target database name (defaults to the configured DATABASE_NAME).",
        )
        parser.add_argument(
            "--skip-safety-backup",
            action="store_true",
            help=(
                "Skip the automatic pre-restore safety backup (use only when "
                "the current database is already broken or empty)."
            ),
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Proceed even if active connections to the target are detected.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Non-interactive confirmation that this destructive operation is intended.",
        )

    def _confirmed(self, options, config, target, path):
        """Require explicit operator confirmation before a destructive restore."""
        if options["yes"]:
            return True
        if sys.stdin is not None and sys.stdin.isatty():
            self.stdout.write(
                self.style.WARNING("WARNING: This operation is DESTRUCTIVE.")
            )
            self.stdout.write(f"  Backup : {path.name}")
            self.stdout.write(
                f"  Target : {target} (host {config['host']}:{config['port']}, "
                f"user {config['user']})"
            )
            self.stdout.write(
                "A fresh safety backup of the current target will be created first."
            )
            answer = input("Type 'RESTORE' to continue: ").strip()
            return answer == "RESTORE"
        return False

    def handle(self, *args, **options):
        config = db.get_db_config()
        password = db.get_db_password()
        try:
            backup_name = db.validate_backup_name(options["backup"])
            path = db.backup_dir() / backup_name
            if not path.is_file():
                raise db.BackupNotFoundError(
                    f"Backup not found in {db.backup_dir()}: {backup_name}"
                )
            target = db.validate_target_name(options["target"] or config["name"])
            if not self._confirmed(options, config, target, path):
                raise CommandError(
                    "Restore aborted: explicit confirmation is required (pass --yes)."
                )
            result = db.restore_backup(
                path,
                config,
                password,
                target,
                skip_safety_backup=options["skip_safety_backup"],
                force=options["force"],
            )
        except db.DatabaseBackupError as exc:
            raise CommandError(str(exc))

        self.stdout.write(
            self.style.SUCCESS(f"Restore of {backup_name} into {target} completed.")
        )
        safety = result["safety_backup"]
        if safety:
            self.stdout.write(
                f"Pre-restore safety backup: {safety['filename']} "
                "(preserve it until the restore is confirmed)."
            )
        verification = result["verification"]
        self.stdout.write(
            f"Tables: {verification['table_count']}; "
            f"migrations applied: {verification['migration_count']}"
        )
        counts = ", ".join(
            f"{label}={count}"
            for label, count in verification["core_counts"].items()
            if count is not None
        )
        if counts:
            self.stdout.write(f"Core record counts: {counts}")
