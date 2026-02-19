from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase

from apps.employees.models import Department, Employee
from apps.employees.signals import create_employee_profile
from apps.rooms.forms import CleaningTaskForm
from apps.rooms.models import CleaningTask, Room, RoomType


class CleaningTaskModelTest(TestCase):
    """Test para las validaciones del formulario de CleaningTaskForm"""

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
            status=Room.StatusChoices.DIRTY,
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

    def test_form_valid_data(self):
        """Formulario con datos válidos para ser aceptado"""

        form_data = {
            "room": self.room.id,
            "assigned_to": self.employee.id,
            "cleaning_type": CleaningTask.TypeChoices.CHECKOUT,
            "priority": 1,
            "notes": "Limpieza después de check-out",
        }

        form = CleaningTaskForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_filters_only_dirty_rooms(self):
        """El formulario debe mostrar solo habitaciones que necesitan limpieza"""

        clean_room = Room.objects.create(
            number="111",
            floor=1,
            room_type=self.room_type,
            status=Room.StatusChoices.CLEAN,
        )

        form = CleaningTaskForm()

        # La habitación limpia NO debe estar en las opciones
        room_ids = [room.id for room in form.fields["room"].queryset]
        self.assertNotIn(clean_room.id, room_ids)

        # La habitación sucia SÍ debe estar
        self.assertIn(self.room.id, room_ids)
