"""Enforce backup retention by removing the oldest backups (Phase 16).

Runs as a dry-run by default so expired backups are only listed, never
deleted, unless ``--execute`` is passed. Only files matching the strict
timestamped backup naming convention are ever considered for deletion.
"""

from django.core.management.base import BaseCommand, CommandError

from apps.common import database_backup as db


class Command(BaseCommand):
    help = (
        "Remove expired backups, keeping the newest N (retention). "
        "Defaults to a dry-run; pass --execute to actually delete."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep",
            type=int,
            default=10,
            help="Number of newest backups to keep (default: 10).",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Actually delete expired backups (default is dry-run).",
        )

    def handle(self, *args, **options):
        directory = db.backup_dir()
        try:
            removed = db.cleanup_backups(
                directory,
                keep=options["keep"],
                dry_run=not options["execute"],
            )
        except db.DatabaseBackupError as exc:
            raise CommandError(str(exc))

        entries = db.list_backups(directory)
        self.stdout.write(
            f"Backups available: {len(entries)} (keeping newest {options['keep']})."
        )
        if not removed:
            self.stdout.write("Nothing to remove.")
            return
        verb = "removed" if options["execute"] else "would remove"
        for filename in removed:
            self.stdout.write(f"{verb}: {filename}")
        if not options["execute"]:
            self.stdout.write(
                "Dry-run only. Re-run with --execute to delete the listed backups."
            )
