from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User Model for Saamu Tailors.
    Provides extensible foundation for future role-based access control and profile fields.
    """

    phone_number = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username or self.email or f"User {self.id}"
