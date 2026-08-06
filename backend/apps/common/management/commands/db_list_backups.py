"""List available PostgreSQL backups in the configured backup directory."""

from django.core.management.base import BaseCommand

from apps.common import database_backup as db


class Command(BaseCommand):
    help = "List available PostgreSQL backups, newest first."

    def handle(self, *args, **options):
        directory = db.backup_dir()
        entries = db.list_backups(directory)
        if not entries:
            self.stdout.write("No backups found.")
            return
        self.stdout.write(f"Backup directory: {directory}")
        for entry in entries:
            size_kb = entry["size_bytes"] / 1024
            modified = entry["modified_at"].strftime("%Y-%m-%d %H:%M:%S")
            self.stdout.write(f"{entry['filename']}  ({size_kb:.1f} KB, {modified})")
