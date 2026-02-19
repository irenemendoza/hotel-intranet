from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.test import TestCase

from apps.employees.models import Department, Employee
from apps.employees.signals import create_employee_profile
from apps.leave.models import Leave


class LeaveModelTest(TestCase):
    """Tests para el modelo Leave"""

    @classmethod
    def setUpClass(cls):
        """Desconectar la señal para TODOS los tests de esta clase"""
        super().setUpClass()
        post_save.disconnect(create_employee_profile, sender=User)

    @classmethod
    def tearDownClass(cls):
        """Reconectar la señal después de todos los tests"""
        super().tearDownClass()
        post_save.connect(create_employee_profile, sender=User)

    def setUp(self):
        self.user = User.objects.create_user(
            username="limpieza",
        )
        self.department = Department.objects.create(
            name="Limpieza",
            code="LIM",
        )
        self.employee = Employee.objects.create(
            user=self.user,
            department=self.department,
            role=Employee.RoleChoices.HOUSEKEEPER,
        )

    def test_end_date_must_be_after_start_date(self):
        """La fecha de fin debe ser posterior o igual a la fecha de inicio"""

        leave = Leave(
            employee=self.employee,
            leave_type=Leave.LeaveTypeChoices.SICK,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=-2),
            reason="sick",
        )

        with self.assertRaises(ValidationError) as context:
            leave.full_clean()

        self.assertIn("__all__", context.exception.message_dict)

    def test_duration_days_calculation(self):
        leave = Leave.objects.create(
            employee=self.employee,
            leave_type=Leave.LeaveTypeChoices.SICK,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            reason="sick",
        )

        self.assertEqual(leave.duration_days(), 3)
