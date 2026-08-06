"""Create a timestamped PostgreSQL custom-format backup (Phase 16)."""

from django.core.management.base import BaseCommand, CommandError

from apps.common import database_backup as db


class Command(BaseCommand):
    help = (
        "Create a timestamped PostgreSQL custom-format backup in the "
        "configured BACKUP_DIR and verify it is usable."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--comment",
            default="",
            help="Optional comment embedded in the backup catalog.",
        )
        parser.add_argument(
            "--no-verify",
            action="store_true",
            help="Skip post-backup verification (not recommended).",
        )

    def handle(self, *args, **options):
        config = db.get_db_config()
        password = db.get_db_password()
        try:
            result = db.create_backup(
                config,
                password,
                comment=options["comment"] or None,
                verify=not options["no_verify"],
            )
        except db.DatabaseBackupError as exc:
            raise CommandError(str(exc))

        self.stdout.write(self.style.SUCCESS(f"Backup created: {result['filename']}"))
        self.stdout.write(f"Size: {result['size']} bytes")
        verification = result.get("verification")
        if verification:
            self.stdout.write(
                "Verification: archive inspectable by PostgreSQL tooling "
                f"({verification['size_bytes']} bytes)"
            )
        else:
            self.stdout.write("Verification: skipped")
