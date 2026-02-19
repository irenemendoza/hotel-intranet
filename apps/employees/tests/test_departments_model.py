from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.employees.models import Department


class DepartmentModelTest(TestCase):
    """Tests para el modelo Department"""

    def test_department_code_must_be_uppercase(self):
        """El código del departamento debe convertirse a mayúsculas automáticamente"""
        dept = Department.objects.create(
            name="Recepción",
            code="rec",
        )
        self.assertEqual(dept.code, "REC")

    def test_department_code_validation(self):
        """El código debe tener exáctamente 3 letras mayúsculas"""
        dept = Department(name="Test", code="AB")
        with self.assertRaises(ValidationError) as context:
            dept.full_clean()

        self.assertIn("code", context.exception.message_dict)

    def test_department_code_unique(self):
        """Lós códigos de departamento deben ser únicos"""
        Department.objects.create(
            name="limpieza",
            code="AAA",
        )

        dept2 = Department(
            name="Mantenimiento",
            code="AAA",
        )

        with self.assertRaises(ValidationError) as context:
            dept2.validate_unique()

        self.assertIn("code", context.exception.message_dict)
