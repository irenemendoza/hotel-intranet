from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase

from apps.employees.signals import create_employee_profile
from apps.rooms.forms import MaintenanceRequestForm
from apps.rooms.models import MaintenanceTask, Room, RoomType


class MaintenanceRequestFormTest(TestCase):
    """Tests para validaciones del formulario MaintenanceRequestForm"""

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
            status=Room.StatusChoices.MAINTENANCE,
        )

        self.user = User.objects.create_user(
            username="receptionist", password="pass123"
        )

    def test_form_valid_data(self):
        """Formulario con datos válido debe ser aceptado"""

        form_data = {
            "room": self.room.id,
            "title": "No funciona la cisterna",
            "description": "Se ha roto el botón",
            "priority": MaintenanceTask.PriorityChoices.HIGH,
        }

        form = MaintenanceRequestForm(form_data)

        self.assertTrue(form.save())

    def test_form_saves_reported_by_user(self):
        """El formulario debe guardar quién reportó el problema"""

        form_data = {
            "room": self.room.id,
            "title": "No funciona la cisterna",
            "description": "Se ha roto el botón",
            "priority": MaintenanceTask.PriorityChoices.HIGH,
        }

        form = MaintenanceRequestForm(form_data)

        self.assertTrue(form.is_valid())
        task = form.save(user=self.user)

        self.assertEqual(task.reported_by, self.user)
        self.assertEqual(task.status, MaintenanceTask.StatusChoices.PENDING)
