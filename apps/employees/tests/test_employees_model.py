from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase
from django.utils import timezone

from apps.attendance.models import Attendance
from apps.employees.models import Department, Employee
from apps.employees.signals import create_employee_profile


class EmployeeModelTest(TestCase):
    """Tests para el modelo Employee"""

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
        """Configuración inicial para cada test"""

        self.department = Department.objects.create(name="Recepción", code="REC")
        self.user = User.objects.create_user(
            username="jperez",
            email="jperez@hotel.com",
            first_name="Juan",
            last_name="Pérez",
        )

        self.employee = Employee.objects.create(
            user=self.user,
            department=self.department,
            role=Employee.RoleChoices.RECEPTIONIST,
        )

    def test_employee_creation(self):
        """Se puede crear un empleado correctamente"""

        self.assertEqual(self.employee.get_full_name(), "Juan Pérez")
        self.assertTrue(self.employee.is_available)

    def test_employee_assigned_to_groups(self):
        """El empleado debe asignarse automáticamente a grupos según sun rol"""

        # Asignar un rol al empleado
        self.employee.role = Employee.RoleChoices.RECEPTIONIST
        self.employee.save()

        # LLamar al método que asigna grupos
        self.employee.assign_to_group()

        # Verificar que se asignó al grupo recepción
        self.assertTrue(self.user.groups.filter(name="Reception").exists())

        # Verificar que tiene 1 grupo
        self.assertEqual(self.user.groups.count(), 1)

    def test_is_supervisor_method(self):
        # Receptionist no es supervisor
        self.assertFalse(self.employee.is_supervisor())

        # Director sí es supervisor
        director_user = User.objects.create_user(
            username="jose",
            email="jdirector@hotel.como",
            first_name="jose",
            last_name="nuñez",
        )
        director = Employee.objects.create(
            user=director_user,
            role=Employee.RoleChoices.DIRECTOR,
            department=self.department,
        )

        self.assertTrue(director.is_supervisor())

    def test_is_checked_in_method(self):
        """El metódo is_checked_in debe indicar si el empleado tiene un registro de asistencia activo"""

        # Sin check-in
        self.assertFalse(self.employee.is_checked_in())

        # Con check-in
        Attendance.objects.create(
            employee=self.employee,
            check_in=timezone.now(),
            status=Attendance.StatusChoices.PRESENT,
        )

        self.assertTrue(self.employee.is_checked_in())
