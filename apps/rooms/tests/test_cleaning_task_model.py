from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase

from apps.employees.models import Department, Employee
from apps.employees.signals import create_employee_profile
from apps.rooms.models import CleaningTask, Room, RoomType


class CleaningTaskModelTest(TestCase):
    """Test del modelo Cleaning Task"""

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
        """Configuración inicial"""

        self.room_type = RoomType.objects.create(
            name="Double",
            code="DBL",
            capacity=2,
        )

        self.room = Room.objects.create(
            number="101",
            floor=1,
            room_type=self.room_type,
        )

        self.user = User.objects.create_user(
            username="jperez",
        )

        self.department = Department.objects.create(name="Housekeeping", code="HKG")

        self.employee = Employee.objects.create(
            user=self.user,
            department=self.department,
            role=Employee.RoleChoices.HOUSEKEEPER,
        )

    def test_cleaning_task_creation(self):
        """Se puede crear una tarea de limpieza correctamente"""
        task = CleaningTask.objects.create(
            room=self.room,
            assigned_to=self.employee,
        )

        self.assertTrue(task)
