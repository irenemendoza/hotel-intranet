from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase

from apps.employees.models import Department, Employee
from apps.employees.signals import create_employee_profile
from apps.rooms.forms import RoomTypeForm
from apps.rooms.models import MaintenanceTask, Room, RoomType


class RoomTypeFormTest(TestCase):
    """Tests para el formulario RoomTypeForm"""

    def test_code_converted_to_uppercase(self):
        """El código debe convertirse a mayúsculas"""

        form_data = {
            "name": "Double",
            "code": "dou",
            "capacity": 2,
            "description": "Habitación doble",
            "amenities": "Aromaterapia",
            "is_active": True,
        }

        form = RoomTypeForm(data=form_data)
        self.assertTrue(form.is_valid())

        self.assertEqual(form.cleaned_data["code"], "DOU")

    def test_code_alphanumeric_and_hyphens(self):
        """El cósigo solo debe permitir alfanuméricos y guiones"""

        form_data = {
            "name": "Double",
            "code": "dou@",
            "capacity": 2,
            "description": "Habitación doble",
            "amenities": "Aromaterapia",
            "is_active": True,
        }

        form = RoomTypeForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("code", form.errors)
