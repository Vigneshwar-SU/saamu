import os

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from apps.authentication.models import Role, User


class Command(BaseCommand):
    """Create (or update) the initial OWNER application-role user.

    There is no public registration, so the first OWNER account is created
    from the command line. Credentials may be supplied as options or via the
    OWNER_USERNAME / OWNER_PASSWORD environment variables.
    """

    help = "Create the initial OWNER application user for Saamu Tailors."

    def add_arguments(self, parser):
        parser.add_argument("--username", default=None, help="OWNER username.")
        parser.add_argument("--password", default=None, help="OWNER password.")
        parser.add_argument(
            "--superuser",
            action="store_true",
            help="Also make this account a Django superuser (Django admin access).",
        )

    def handle(self, *args, **options):
        username = options.get("username") or os.getenv("OWNER_USERNAME") or "owner"
        password = options.get("password") or os.getenv("OWNER_PASSWORD")

        if not password:
            raise CommandError(
                "A password is required. Pass --password or set OWNER_PASSWORD."
            )

        defaults = {"role": Role.OWNER, "is_active": True}
        if options.get("superuser"):
            defaults["is_superuser"] = True
            defaults["is_staff"] = True

        try:
            user, created = User.objects.get_or_create(
                username=username, defaults=defaults
            )
        except IntegrityError as exc:
            raise CommandError(
                f"Could not create OWNER user '{username}': {exc}"
            ) from exc

        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created OWNER user '{user.username}' (id={user.id})."
                )
            )
        else:
            if user.role != Role.OWNER:
                user.role = Role.OWNER
                user.save(update_fields=["role"])
            self.stdout.write(
                self.style.WARNING(
                    f"OWNER user '{user.username}' already exists (id={user.id}); "
                    "password unchanged. Use Django shell or admin to change it."
                )
            )
