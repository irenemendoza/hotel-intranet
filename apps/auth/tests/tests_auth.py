from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import Client, TestCase
from django.urls import reverse

from apps.employees.models import Department, Employee
from apps.employees.signals import create_employee_profile


class AuthenticationTest(TestCase):
    """Tests para autenticación y permisos"""

    def setUp(self):
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

        cliente = Client()

        self.department = Department.objects.create(name="Housekeeping", code="HKG")

        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@hotel.com"
        )

        self.department = Department.objects.create(name="Housekeeping", code="HKG")

        self.employee = Employee.objects.create(
            user=self.user,
            department=self.department,
            role=Employee.RoleChoices.HOUSEKEEPER,
        )

    def test_login_successful(self):
        """Login con credenciales correctas debe funcionar"""
        response = self.client.post(
            reverse("auth:login"), {"username": "testuser", "password": "testpass123"}
        )

        self.assertEqual(response.status_code, 302)

    def test_login_failed_wrong_password(self):
        """Login con contraseña incorrecta debe fallar"""
        response = self.client.post(
            reverse("auth:login"), {"username": "testuser", "password": "wrongpassword"}
        )

        self.assertEqual(response.status_code, 200)

    def test_protected_view_requires_login(self):
        """Las vistas protegidas deben requerir autenticación"""
        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_authenticated_user_can_access_dashboard(self):
        """Usuario autenticado puede acceder al dashboard"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)
