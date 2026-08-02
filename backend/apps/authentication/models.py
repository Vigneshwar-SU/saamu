from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    """
    Application roles for Saamu Tailors.

    Exactly two roles exist:
    - OWNER: can log in and view permitted business information (view-only).
    - STAFF: the operational management user for business operations.

    These are application roles, independent of Django's ``is_staff`` flag.
    """

    OWNER = "OWNER", "Owner"
    STAFF = "STAFF", "Staff"


class User(AbstractUser):
    """
    Custom User Model for Saamu Tailors.

    Provides an explicit application ``role`` (OWNER/STAFF) used for
    role-based access control. Django's ``is_staff`` / ``is_superuser``
    flags are unrelated to the application role and never become a third role.
    """

    phone_number = models.CharField(max_length=20, blank=True, null=True)

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STAFF,
        help_text="Application role used for role-based access control.",
    )

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username or self.email or f"User {self.id}"
