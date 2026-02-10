# apps/attendance/tests/test_models.py
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.attendance.models import Attendance
from apps.employees.models import Department, Employee


class AttendanceCheckInViewTest(TestCase):
    """Tests para la vista CheckIn del Attendance"""

    def setUp(self):
        """Configuración inicial ejecutada antes de cada test"""
        self.department = Department.objects.create(
            name="Recepción", code="REC", color="#3B82F6"
        )

        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            first_name="Juan",
            last_name="Pérez",
        )

        self.employee = Employee.objects.create(
            user=self.user,
            department=self.department,
            role="recepcionista",
            employee_number="EMP001",
        )

    def test_duration_calculation_with_checkout(self):
        """Verifica que duration() calcula correctamente las horas trabajadas"""
        # Crear asistencia con 8 horas de trabajo
        now = timezone.now()
        attendance = Attendance.objects.create(
            employee=self.employee, check_in=now - timedelta(hours=8), check_out=now
        )

        duration = attendance.duration()
        hours = duration.total_seconds() / 3600

        self.assertAlmostEqual(hours, 8.0, places=1)

    def test_duration_calculation_without_checkout(self):
        """Verifica que duration() usa la hora actual cuando no hay check_out"""
        # Crear asistencia hace 5 horas sin check_out
        attendance = Attendance.objects.create(
            employee=self.employee, check_in=timezone.now() - timedelta(hours=5)
        )

        duration = attendance.duration()
        hours = duration.total_seconds() / 3600

        # Debería ser aproximadamente 5 horas
        self.assertAlmostEqual(hours, 5.0, places=0)
