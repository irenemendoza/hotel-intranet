from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Attendance(models.Model):
    """Employee clock-in and clock-out records"""

    class StatusChoices(models.TextChoices):
        PRESENT = "present", _("Present")
        LATE = "late", _("Late")
        ABSENT = "absent", _("Absent")
        HALF_DAY = "half_day", _("Half day")

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name=_("Employee"),
    )
    check_in = models.DateTimeField(_("Check-in time"), default=timezone.now)
    check_out = models.DateTimeField(_("Check-out time"), null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PRESENT,
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Attendance")
        verbose_name_plural = _("Attendances")
        ordering = ["-check_in"]
        indexes = [
            models.Index(fields=["employee", "-check_in"]),
            models.Index(fields=["check_in"]),
        ]
        constraints = [
            # Only one open attendance per employee
            models.UniqueConstraint(
                fields=["employee"],
                condition=models.Q(check_out__isnull=True),
                name="unique_open_attendance_per_employee",
            ),
            # Check-out always after check-in
            models.CheckConstraint(
                condition=models.Q(check_out__gte=models.F("check_in"))
                | models.Q(check_out__isnull=True),
                name="check_out_after_check_in",
            ),
        ]

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.check_in.strftime('%d/%m/%Y %H:%M')}"

    @property
    def duration(self):
        """Calculates shift duration"""
        if self.check_out:
            return self.check_out - self.check_in
        return timezone.now() - self.check_in

    @property
    def duration_formatted(self):
        """Returns duration in readable format"""
        duration = self.duration
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        return f"{hours}h {minutes}m"

    def is_overtime(self, standard_hours=8):
        """_('Check if there are overtime hours (more than 8 hours)')"""
        if self.check_out:
            hours = self.duration().total_seconds() / 3600
            return hours > standard_hours
        return False

    @classmethod
    def create_check_in(cls, employee):
        """Creates check-in attendance"""
        # Verify there isn't any attendance already open
        open_attendance = cls.objects.filter(
            employee=employee, check_out__isnull=True
        ).first()

        if open_attendance:
            raise ValidationError(_("Employee already has an open attendance"))

        return cls.objects.create(
            employee=employee,
            check_in=timezone.now(),
        )

    def process_check_out(self):
        """Processes check-out"""
        if self.check_out:
            raise ValidationError(_("Attendance already checked out"))

        self.check_out = timezone.now()
        self.save()
