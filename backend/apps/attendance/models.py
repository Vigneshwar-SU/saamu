"""Tailor attendance records.

Attendance is a simple daily status record per tailor. There is exactly one
record per tailor per date (enforced by a unique constraint). Records are
never physically deleted, so historical attendance stays visible even after a
tailor is archived. Missing records are never treated as PRESENT — aggregation
only counts records that actually exist.
"""

from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.tailors.models import Tailor


class Attendance(TimeStampedModel):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        HALF_DAY = "HALF_DAY", "Half Day"

    tailor = models.ForeignKey(
        Tailor,
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )
    attendance_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices)
    notes = models.TextField(blank=True, default="")
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="marked_attendance_records",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-attendance_date", "-created_at"]
        verbose_name = "Attendance"
        verbose_name_plural = "Attendance Records"
        constraints = [
            models.UniqueConstraint(
                fields=["tailor", "attendance_date"],
                name="unique_attendance_per_tailor_date",
            )
        ]
        indexes = [
            models.Index(fields=["attendance_date"]),
            models.Index(fields=["tailor", "attendance_date"]),
        ]

    def __str__(self):
        return f"{self.tailor.full_name} - {self.attendance_date} ({self.get_status_display()})"
