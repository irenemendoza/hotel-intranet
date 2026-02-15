from datetime import timedelta

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Department(models.Model):
    class ColorChoices(models.TextChoices):
        BLUE = "#3B82F6", _("Blue")
        GREEN = "#10B981", _("Green")
        YELLOW = "#F59E0B", _("Yellow")
        RED = "#EF4444", _("Red")
        PURPLE = "#8B5CF6", _("Purple")
        PINK = "#EC4899", _("Pink")
        ORANGE = "#F97316", _("Orange")
        CYAN = "#06B6D4", _("Cyan")
        INDIGO = "#6366F1", _("Indigo")
        LIME = "#84CC16", _("Lima")
        EMERALD = "#059669", _("Emerald")
        GREY = "#6B7280", _("Grey")

    # Hotel departments
    name = models.CharField(
        _("Name"),
        max_length=50,
    )
    color = models.CharField(
        _("Color"),
        max_length=7,
        choices=ColorChoices.choices,
        default=ColorChoices.BLUE,
    )
    code = models.CharField(
        _("Code"),
        max_length=3,
        unique=True,
        validators=[
            RegexValidator(
                regex="^[A-Z]{3}$",
                message="Code must be exactly 3 uppercase letters",
                code="invalid_code",
            )
        ],
        help_text="3 uppercase letters code (e.g. : DIR, REC, LIM)",
    )
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.upper()
        self.full_clean()
        super().save(*args, **kwargs)


class Employee(models.Model):
    class RoleChoices(models.TextChoices):
        # Direction
        DIRECTOR = "director", _("Director")

        # Reception
        RECEPTION_MANAGER = "reception_manager", _("Reception Manager")
        RECEPTIONIST = "receptionist", _("Recepcionist")

        # Housekeeping
        HOUSEKEEPING_MANAGER = "housekeeping_manager", _("Housekeeping Manager")
        HOUSEKEEPER = "housekeeper", _("Housekeeper")

        # Maintenance
        MAINTENANCE_MANAGER = "maintenance_manager", _("Maintenance Manager")
        MAINTENANCE = "maintenance_staff", _("Maintenance Staff")

        # RRHH
        RRHH = "rrhh", _("Human Resources")

    # User profile with hotel information
    user = models.OneToOneField(
        User, verbose_name=_("User"), on_delete=models.CASCADE, related_name="employee"
    )
    department = models.ForeignKey(
        Department,
        verbose_name=_("Departament"),
        on_delete=models.PROTECT,
    )
    role = models.CharField(
        _("Role"),
        max_length=30,
        choices=RoleChoices.choices,
        help_text="Employee role in the hotel",
    )
    phone = models.CharField(_("Phone"), max_length=20, blank=True)

    avatar = models.ImageField(_("Avatar"), upload_to="avatars/", blank=True, null=True)
    employee_number = models.CharField(
        _("Employee number"), max_length=20, unique=True, blank=True, null=True
    )
    hire_date = models.DateField(_("Hire date"), null=True, blank=True)
    is_available = models.BooleanField(
        _("Available"),
        default=True,
        help_text=_("Indicates if the employee is available for assignments"),
    )
    bio = models.TextField(
        _("Biography"), blank=True, help_text=_("Additional employee information")
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Last updated"), auto_now=True)

    class Meta:
        verbose_name = _("Employee Profile")
        verbose_name_plural = _("Employee Profiles")

    def __str__(self):
        return f"{self.get_full_name()} - {self.get_role_display()}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.assign_to_group()

    def assign_to_group(self):
        """Assigns the user to the corresponding group based on their role"""
        from django.contrib.auth.models import Group

        # Role to group mapping
        role_group_map = {
            "director": ["Management", "Supervisors"],
            "reception_manager": ["Reception", "Supervisors"],
            "recepcionist": ["Reception"],
            "housekeeping_manager": ["Housekeeping", "Supervisors"],
            "housekeeper": ["Housekeeping"],
            "maitenance_manager": ["Maitenance", "Supervisors"],
            "mantenance": ["Maitenance"],
            "rrhh": ["RRHH", "Supervisors"],
        }

        groups = role_group_map.get(self.role, [])
        self.user.groups.clear()

        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            self.user.groups.add(group)

    def is_supervisor(self):
        """Checks if the user is a supervisor/manager"""
        return self.role in [
            "director",
            "reception_manager",
            "housekeeping_manager",
            "maintenance_manager",
            "rrhh",
        ]

    def can_manage_team(self):
        """Checks if they can manage their team"""
        return self.is_supervisor()

    def get_supervised_employees(self):
        """Gets the employees under their supervision"""
        if not self.can_manage_team():
            return Employee.objects.none()

        # Mapping of managers to their subordinates
        supervision_map = {
            "director": Employee.objects.all(),  # Sees everyone
            "reception_manager": Employee.objects.filter(role="receptionist"),
            "housekeeper_manager": Employee.objects.filter(role="housekeeper"),
            "maintenance_manager": Employee.objects.filter(role="maintenance"),
            "rrhh": Employee.objects.all(),  # Sees everyone
        }

        return supervision_map.get(self.role, Employee.objects.none())

    def get_full_name(self):
        return self.user.get_full_name() or self.user.username

    def get_current_attendance(self):
        """Gets the current active attendance (without check_out)"""
        return self.attendances.filter(check_out__isnull=True).first()

    def is_checked_in(self):
        """Gets if the employee is currently clocked in"""
        return self.get_current_attendance() is not None

    def get_today_work_hours(self):
        """Calculates hours worked today"""
        today = timezone.now().date()
        attendances = self.attendances.filter(check_in__date=today)

        total_hours = timedelta()
        for attendance in attendances:
            if attendance.check_out:
                total_hours += attendance.duration()

        return total_hours
