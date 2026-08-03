"""Serializers for tailor attendance records."""

from rest_framework import serializers

from apps.tailors.models import Tailor
from apps.tailors.serializers import TailorSerializer

from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    tailor = serializers.PrimaryKeyRelatedField(queryset=Tailor.objects.all())

    class Meta:
        model = Attendance
        fields = [
            "id",
            "tailor",
            "attendance_date",
            "status",
            "notes",
            "marked_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "marked_by", "created_at", "updated_at"]

    def validate(self, attrs):
        tailor = attrs.get("tailor") or getattr(self.instance, "tailor", None)
        attendance_date = attrs.get("attendance_date") or getattr(
            self.instance, "attendance_date", None
        )
        if tailor is not None and attendance_date is not None:
            qs = Attendance.objects.filter(
                tailor=tailor, attendance_date=attendance_date
            )
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {
                        "attendance_date": (
                            "Attendance for this tailor on this date already exists."
                        )
                    }
                )
        return attrs

    def get_unique_together_validators(self):
        """The unique (tailor, attendance_date) constraint is validated in
        ``validate`` so the duplicate error surfaces on ``attendance_date``."""
        return []

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["tailor"] = TailorSerializer(instance.tailor, context=self.context).data
        ret["marked_by_name"] = (
            instance.marked_by.username if instance.marked_by else None
        )
        return ret
