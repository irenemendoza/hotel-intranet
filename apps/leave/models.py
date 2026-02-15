from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _

from apps.employees.models import Employee


class Leave(models.Model):
    """Leave and vacation management"""

    class LeaveTypeChoices(models.TextChoices):
        VACATION = "vacation", _("Vacation")
        SICK = "sick", _("Sick")
        PERSONAL = "personal", _("Personal")
        UNPAID = "unpaid", _("Unpaid")
        OTHER = "other", _("Other")

    class StatusChoices(models.TextChoices):
        PENDING = "pending", _("Pending")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")
        CANCELLED = "cancelled", _("Cancelled")

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leaves",
        verbose_name=_("Employee"),
    )
    leave_type = models.CharField(
        _("Leave_type"), max_length=20, choices=LeaveTypeChoices.choices
    )
    start_date = models.DateField(_("Start date"))
    end_date = models.DateField(_("End date"))
    reason = models.TextField(_("Reason"))
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_leaves",
        verbose_name=_("Approved by"),
    )
    approved_at = models.DateTimeField(_("Approval date"), null=True, blank=True)
    rejection_reason = models.TextField(_("Rejection reason"), blank=True)
    attachment = models.FileField(
        _("Attachment"),
        upload_to="leaves/",
        blank=True,
        null=True,
        help_text=_("Supporting document"),
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Last updated"), auto_now=True)

    class Meta:
        verbose_name = _("Leave")
        verbose_name_plural = _("Leaves")
        ordering = ["-created_at"]

        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gte=F("start_date")),
                name="valid_leave_date_range",
            )
        ]

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_leave_type_display()} ({self.start_date} - {self.end_date})"

    def duration_days(self):
        """Calculates duration in days"""
        return (self.end_date - self.start_date).days + 1
