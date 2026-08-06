"""Verify a PostgreSQL backup archive and optionally test-restore it."""

from django.core.management.base import BaseCommand, CommandError

from apps.common import database_backup as db


class Command(BaseCommand):
    help = (
        "Verify that a backup exists, is non-empty and can be inspected by "
        "PostgreSQL tooling. With --restore-test it is also restored into a "
        "disposable database and representative row counts are compared."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--backup",
            default=None,
            help="Backup filename to verify (defaults to the newest backup).",
        )
        parser.add_argument(
            "--restore-test",
            action="store_true",
            help="Also restore into a disposable database and compare counts.",
        )

    def handle(self, *args, **options):
        config = db.get_db_config()
        password = db.get_db_password()
        try:
            entries = db.list_backups()
            if not entries:
                raise db.BackupError(
                    "No backups found in the configured backup directory."
                )
            backup_name = options["backup"]
            if backup_name:
                db.validate_backup_name(backup_name)
                path = db.backup_dir() / backup_name
                if not path.is_file():
                    raise db.BackupNotFoundError(f"Backup not found: {backup_name}")
            else:
                path = entries[0]["path"]
            result = db.verify_backup(
                path,
                config,
                password,
                restore_test=options["restore_test"],
            )
        except db.DatabaseBackupError as exc:
            raise CommandError(str(exc))

        self.stdout.write(self.style.SUCCESS(f"Backup verified: {result['filename']}"))
        self.stdout.write(
            f"Size: {result['size_bytes']} bytes; "
            f"archive inspectable: {result['archive_inspectable']}"
        )
        if "restore_test" in result:
            restore_test = result["restore_test"]
            self.stdout.write(
                f"Restore test into '{restore_test['database']}': "
                f"{len(restore_test['comparisons'])} tables compared, "
                f"{len(restore_test['mismatches'])} mismatches"
            )
            if restore_test["mismatches"]:
                tables = ", ".join(
                    mismatch["table"] for mismatch in restore_test["mismatches"]
                )
                raise CommandError(f"Restore test found count mismatches: {tables}")
