from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.employees.models import Employee


class RoomType(models.Model):
    """Room type (Single, Double, Suite...)"""

    name = models.CharField(_("Name"), max_length=50)
    code = models.CharField(_("Code"), max_length=10, unique=True)
    capacity = models.PositiveIntegerField(
        _("Capacity"), help_text="Maximum capacity number"
    )
    description = models.TextField(_("Description"), blank=True)
    amenities = models.TextField(
        _("Amenities"), blank=True, help_text="Amenities included"
    )
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Room Type")
        verbose_name_plural = _("Room Types")

    def __str__(self):
        return f"{self.name} ({self.code})"


class Reservation(models.Model):
    """Room reservation"""

    class StatusChoices(models.TextChoices):
        PENDING = "pending", _("Pending")
        CONFIRMED = "confirmed", _("Confirmed")
        PENDING_CHECKIN = "pending_checkin", _("Pending check-in")
        CHECKED_IN = "checked_in", _("Checked in")
        PENDING_CHECKOUT = "pending_checkout", _("Pending check-out")
        CHECKED_OUT = "checked_out", _("Checked out")
        CANCELLED = "cancelled", _("Canceled")
        NO_SHOW = "no_show", _("No show")

    class PaymentStatusChoices(models.TextChoices):
        UNPAID = "unpaid", _("Unpaid")
        PARTIAL = "partial", _("Partial payment")
        PAID = "paid", _("Paid")
        REFUNDED = "refunded", _("Refunded")

    # Reservation information
    reservation_number = models.CharField(
        _("Reservation number"),
        max_length=20,
        unique=True,
        editable=False,
        help_text=_("Auto-generated"),
    )
    room = models.ForeignKey(
        "Room",
        on_delete=models.PROTECT,
        related_name="reservations",
        verbose_name=_("Room"),
    )

    # Dates
    check_in_date = models.DateField(_("Check-in date"))
    check_out_date = models.DateField(_("Check-out date"))
    actual_check_in = models.DateTimeField(
        _("Actual check-in"),
        null=True,
        blank=True,
        help_text=_("Actual check-in date and time"),
    )
    actual_check_out = models.DateTimeField(
        _("Actual check-out"),
        null=True,
        blank=True,
        help_text=_("Actual check-out date and time"),
    )

    # Guest information
    guest_first_name = models.CharField(_("First name"), max_length=100)
    guest_last_name = models.CharField(_("Last name"), max_length=100)
    guest_email = models.EmailField(_("Email"), help_text=_("Guest's email"))
    guest_phone = models.CharField(_("Phone"), max_length=20)
    guest_dni = models.CharField(
        _("ID/Passport"), max_length=20, blank=True, help_text=_("Identity document")
    )
    guest_nationality = models.CharField(_("Nationality"), max_length=50, blank=True)
    guest_address = models.TextField(_("Address"), blank=True)

    # Reservation details
    adults = models.PositiveIntegerField(
        _("Adults"), default=1, validators=[MinValueValidator(1)]
    )
    children = models.PositiveIntegerField(
        _("Children"), default=0, validators=[MinValueValidator(0)]
    )
    special_requests = models.TextField(
        _("Special requests"), blank=True, help_text=_("Guest's requests")
    )

    # Status and management
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_reservations",
        verbose_name=_("Created by"),
    )
    checked_in_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checkins_processed",
        verbose_name=_("Checked in by"),
    )
    checked_out_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checkouts_processed",
        verbose_name=_("Checked out by"),
    )

    # Financial information
    room_rate = models.DecimalField(
        _("Room rate per night"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    total_amount = models.DecimalField(
        _("Total amount"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        blank=True,
        default=Decimal("0.00"),
    )
    paid_amount = models.DecimalField(
        _("Paid amount"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    payment_status = models.CharField(
        _("Payment status"),
        max_length=20,
        choices=PaymentStatusChoices.choices,
        default=PaymentStatusChoices.UNPAID,
    )

    # Internal notes
    internal_notes = models.TextField(
        _("Internal notes"),
        blank=True,
        help_text=_("Staff notes (not visible to guest)"),
    )
    cancellation_reason = models.TextField(_("Cancellation reason"), blank=True)

    # Metadata
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Last updated"), auto_now=True)

    class Meta:
        verbose_name = _("Reservation")
        verbose_name_plural = _("Reservations")
        ordering = ["-check_in_date", "-created_at"]
        indexes = [
            models.Index(fields=["check_in_date", "check_out_date"]),
            models.Index(fields=["room", "status"]),
            models.Index(fields=["guest_email"]),
            models.Index(fields=["reservation_number"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(check_out_date__gt=F("check_in_date")),
                name="valid_reservation_date_range",
            )
        ]

    def __str__(self):
        return (
            f"{self.reservation_number} - {self.guest_full_name} - {self.room.number}"
        )

    def save(self, *args, **kwargs):
        """Generate reservation number if it doesn't exist"""
        if not self.reservation_number:
            self.reservation_number = self.generate_reservation_number()

        # Calculate total amount automatically
        if not self.total_amount or self.total_amount == 0:
            self.total_amount = self.calculate_total()

        # Update payment status
        self.update_payment_status()

        # Verify validations
        self.full_clean()

        super().save(*args, **kwargs)

    def clean(self):
        """Model validations"""
        super().clean()

        # Validate dates
        if self.check_in_date and self.check_out_date:
            if self.check_out_date <= self.check_in_date:
                raise ValidationError(
                    {"check_out_date": _("Check-out date must be after check-in date")}
                )

        # Validate room capacity
        if self.room:
            total_guests = self.adults + self.children

        # Validate room availability
        if self.room and self.check_in_date and self.check_out_date:
            if not self.is_room_available():
                raise ValidationError(
                    {"room": _("This room is not available for the selected dates")}
                )

    # Calculated properties
    @property
    def guest_full_name(self):
        # Guest's full name
        return f"{self.guest_first_name} {self.guest_last_name}"

    @property
    def nights(self):
        # Number of nights
        if self.check_in_date and self.check_out_date:
            return (self.check_out_date - self.check_in_date).days
        return 0

    @property
    def is_active(self):
        """Checks if reservation is active (guest in-house)"""
        return self.status == self.StatusChoices.CHECKED_IN

    @property
    def is_confirmed(self):
        """Checks if reservation is confirmed"""
        return self.status == self.StatusChoices.CONFIRMED

    @property
    def is_completed(self):
        """Checks if reservation is completed"""
        return self.status == self.StatusChoices.CHECKED_OUT

    @property
    def pending_amount(self):
        """Pending payment amount"""
        return self.total_amount - self.paid_amount

    @property
    def is_paid(self):
        """Checks if fully paid"""
        return self.paid_amount >= self.total_amount

    def nights_stayed(self):
        """Calculates how many nights the guest has stayed"""
        if self.actual_check_in:
            if self.actual_check_out:
                delta = self.actual_check_out - self.actual_check_in
            else:
                delta = timezone.now() - self.actual_check_in
            return delta.days
        return 0

    def needs_linen_change(self):
        """Determines if linen change is needed (every 3 days)"""
        return self.nights_stayed() >= 3

    def get_cleaning_type_needed(self):
        """Determines what type of cleaning is needed"""
        if not self.is_active:
            return None

        today = timezone.now().date()

        # Departure
        if self.check_out_date == today:
            return "checkout"
        # Stay over with linen change
        elif self.needs_linen_change():
            return "deep_cleaning"
        # Normal stay over
        else:
            return "stay_over"

    # Business methods
    def calculate_total(self):
        return self.room_rate * self.nights

    def update_payment_status(self):
        """Updates payment status based on paid amount"""
        if self.paid_amount >= self.total_amount:
            self.payment_status = self.PaymentStatusChoices.PAID
        elif self.paid_amount > 0:
            self.payment_status = self.PaymentStatusChoices.PARTIAL
        else:
            self.payment_status = self.PaymentStatusChoices.UNPAID

    def generate_reservation_number(self):
        """Generates unique reservation number"""
        from datetime import datetime

        from django.utils.crypto import get_random_string

        # Format: RES-YYYYMMDD-XXXX
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = get_random_string(length=4, allowed_chars="0123456789")

        reservation_number = f"RES-{date_str}-{random_str}"

        # Verify it doesn't exist
        while Reservation.objects.filter(
            reservation_number=reservation_number
        ).exists():
            random_str = get_random_string(length=4, allowed_chars="0123456789")
            reservation_number = f"RES-{date_str}-{random_str}"

        return reservation_number

    def is_room_available(self):
        """Checks if room is available for selected dates"""
        # Exclude this reservation if editing
        queryset = Reservation.objects.filter(room=self.room)
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)

        # Look for overlapping reservations
        overlapping = queryset.filter(
            check_in_date__lt=self.check_out_date,
            check_out_date__gt=self.check_in_date,
            status__in=[self.StatusChoices.CONFIRMED, self.StatusChoices.CHECKED_IN],
        )
        return not overlapping.exists()

    def check_in(self, employee):
        """Processes check-in"""
        if self.status != self.StatusChoices.CONFIRMED:
            raise ValidationError(_("Only confirmed reservation can be checked in"))

        self.status = self.StatusChoices.CHECKED_IN
        self.actual_check_in = timezone.now()
        self.checked_in_by = employee

        # Update room status
        self.room.status = Room.StatusChoices.OCCUPIED
        self.room.occupancy = Room.OccupancyChoices.OCCUPIED
        self.room.save()

        self.save()

    def check_out(self, employee):
        """Processes check-out"""
        if self.status != self.StatusChoices.CHECKED_IN:
            raise ValidationError(_("Only checked-in reservations can be checked out"))

        self.status = self.StatusChoices.CHECKED_OUT
        self.actual_check_out = timezone.now()
        self.checked_out_by = employee

        # Update room status
        self.room.status = Room.StatusChoices.DIRTY
        self.room.occupancy = Room.OccupancyChoices.VACANT
        self.room.save()

        # Create cleaning task automatically
        from apps.rooms.models import CleaningTask

        CleaningTask.objects.create(
            room=self.room,
            cleaning_type=CleaningTask.TypeChoices.CHECKOUT,
            priority=1,
            notes=__("Cleaning after checkout -Reservation %(number)s")
            % {"number": self.reservation_number},
        )
        self.save()

    def cancel(self, reason=""):
        """Cancels reservation"""
        if self.status == self.StatusChoices.CHECKED_IN:
            raise ValidationError(_("Cannot cancel a checked-in reservation"))

        self.status = self.StatusChoices.CANCELLED
        self.cancellation_reason = reason

        # Release the room
        if self.room.occupancy == Room.OccupancyChoices.RESERVED:
            self.room.occupancy = Room.OccupancyChoices.VACANT
            self.room.save()

        self.save()

    @property
    def pending_amount_display(self):
        return self.total_amount - self.amount_paid

    def get_status_color(self):
        """Returns bootstrap color based on status"""
        colors = {
            self.StatusChoices.PENDING: "secondary",
            self.StatusChoices.CONFIRMED: "primary",
            self.StatusChoices.CHECKED_IN: "success",
            self.StatusChoices.CHECKED_OUT: "info",
            self.StatusChoices.CANCELLED: "danger",
            self.StatusChoices.NO_SHOW: "warning",
        }
        return colors.get(self.status, "secondary")


class Room(models.Model):
    class StatusChoices(models.TextChoices):
        CLEAN = "clean", _("Clean")
        DIRTY = "dirty", _("Dirty")
        INSPECTED = "inspected", _("Inspected")
        MAINTENANCE = "maintenance", _("Under maintenance")
        OUT_OF_ORDER = "out_of_order", _("Out of order")

    class OccupancyChoices(models.TextChoices):
        VACANT = "vacant", _("Vacant")
        OCCUPIED = "occupied", _("Occupied")
        RESERVED = "reserved", _("Reserved")

    number = models.CharField(_("Number"), max_length=10, unique=True)
    floor = models.PositiveIntegerField(_("Floor"))
    room_type = models.ForeignKey(
        RoomType, on_delete=models.PROTECT, verbose_name=_("Room type")
    )
    status = models.CharField(
        _("Cleaning status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.DIRTY,
    )
    occupancy = models.CharField(
        _("Occupancy status"),
        max_length=20,
        choices=OccupancyChoices.choices,
        default=OccupancyChoices.VACANT,
    )
    last_cleaned = models.DateTimeField(_("Last cleaned"), null=True, blank=True)
    last_inspected = models.DateTimeField(_("Last inspected"), null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Last updated"), auto_now=True)

    class Meta:
        verbose_name = _("Room")
        verbose_name_plural = _("Rooms")
        ordering = ["floor", "number"]

    def __str__(self):
        return _("Room %(number)s - Floor %(floor)s") % {
            "number": self.number,
            "floor": self.floor,
        }

    def get_status_display_color(self):
        """Returns color based on status"""
        colors = {
            self.StatusChoices.CLEAN: "success",
            self.StatusChoices.DIRTY: "warning",
            self.StatusChoices.INSPECTED: "info",
            self.StatusChoices.MAINTENANCE: "danger",
            self.StatusChoices.OUT_OF_ORDER: "dark",
        }
        return colors.get(self.status, "secondary")

    def get_current_reservation(self):
        """Gets current active reservation"""
        return self.reservations.filter(
            status=Reservation.StatusChoices.CHECKED_IN,
            actual_check_in__isnull=False,
            actual_check_out__isnull=True,
        ).first()

    def is_occupied(self):
        """Checks if room is occupied"""
        return self.get_current_reservation() is not None

    def get_next_reservation(self):
        """Gets next confirmed reservation"""
        today = timezone.now().date()
        return (
            self.reservations.filter(
                status=Reservation.StatusChoices.CONFIRMED, check_in_date__gte=today
            )
            .order_by("check_in_date")
            .first()
        )


class CleaningTask(models.Model):
    """Cleaning tasks assigned to rooms"""

    class StatusChoices(models.TextChoices):
        PENDING = "pending", _("Pending")
        IN_PROGRESS = "in_progress", _("In progress")
        COMPLETED = "completed", _("Completed")
        VERIFIED = "verified", _("Verified")

    # Cleaning types
    class TypeChoices(models.TextChoices):
        CHECKOUT = "checkout", _("Checkout")
        STAY_OVER = "stay_over", _("Stay over")
        DEEP_CLEANING = "deep_cleaning", _("Deep cleaning")

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="cleaning_tasks",
        verbose_name=_("Room"),
    )
    assigned_to = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name="cleaning_tasks",
        verbose_name=_("Assigned to"),
    )
    cleaning_type = models.CharField(
        _("Cleaning type"),
        max_length=20,
        choices=TypeChoices.choices,
        default=TypeChoices.CHECKOUT,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    priority = models.PositiveIntegerField(
        _("Priority"), default=1, help_text="1 = Alta, 5 = Baja"
    )
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_cleanings",
        verbose_name=_("Verified by"),
    )
    verified_at = models.DateTimeField(_("Verification date"), null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    photos = models.ImageField(
        _("Photos"), upload_to="cleaning_tasks/", blank=True, null=True
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Last updated"), auto_now=True)
    completed_at = models.DateTimeField(_("Completed at"), auto_now=True)

    class Meta:
        verbose_name = (_("Cleaning Task"),)
        verbose_name_plural = (_("Cleaning Tasks"),)
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.room} - {self.get_status_display()}"


class MaintenanceTask(models.Model):
    """Maintenance requests for rooms"""

    class PriorityChoices(models.TextChoices):
        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")
        URGENT = "urgent", _("Urgent")

    class StatusChoices(models.TextChoices):
        PENDING = "pending", _("Pending")
        ASSIGNED = "assigned", _("Assigned")
        IN_PROGRESS = "in_progress", _("In progress")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="maintenance_requests",
        verbose_name=_("Room"),
    )
    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reported_maintenance",
        verbose_name=_("Reported by"),
    )
    assigned_to = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_maintenance",
        verbose_name=_("Assigned to"),
    )
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"))
    priority = models.CharField(
        _("Priority"),
        max_length=10,
        choices=PriorityChoices.choices,
        default=PriorityChoices.MEDIUM,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    resolution = models.TextField(_("Resolution"), blank=True)
    photos = models.ImageField(
        _("Photos"), upload_to="maintenance/", blank=True, null=True
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Last updated"), auto_now=True)
    assigned_at = models.DateTimeField(_("Assigned to"), null=True, blank=True)
    resolved_at = models.DateTimeField(_("Resolution date"), null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Maintenance Request")
        verbose_name_plural = _("Maintenance Requests")

    def __str__(self):
        return f"{self.room} - {self.title} [{self.get_priority_display()}]"

    def get_priority_color(self):
        """Returns color based on priority"""
        colors = {
            self.PriorityChoices.LOW: "info",
            self.PriorityChoices.MEDIUM: "warning",
            self.PriorityChoices.HIGH: "danger",
            self.PriorityChoices.URGENT: "dark",
        }
        return colors.get(self.priority, "secondary")
