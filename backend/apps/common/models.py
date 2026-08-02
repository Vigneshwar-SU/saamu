"""Shared model utilities for Saamu Tailors."""

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Abstract base with created_at / updated_at timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


def now():
    return timezone.now()
