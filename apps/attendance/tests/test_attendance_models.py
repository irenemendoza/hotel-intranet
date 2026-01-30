# apps/attendance/tests/test_models.py
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.attendance.models import Attendance
from apps.employees.models import Department, Employee


class AttendanceModelTest(TestCase):
    """Tests para el modelo Attendance"""

    """Como en el modelo Employee tengo que se cree automáticamente un empleado tras crearse un user con un post_save, voy a desactivar esta función para los tests"""

    @classmethod
    def setUpClass(cls):
        """Desactivar señales antes de ejecutar los tests"""
        super().setUpClass()
        # Desconectar la señal post_save
        from django.db.models.signals import post_save

        from apps.employees.models import create_employee_profile

        post_save.disconnect(create_employee_profile, sender=User)

    """Quiero que se vuelva a activar el post_save del modelo tras realizar los tests"""

    @classmethod
    def tearDownClass(cls):
        """Reconectar señales después de los tests"""
        super().tearDownClass()
        # Reconectar la señal
        from django.db.models.signals import post_save

        from apps.employees.models import create_employee_profile

        post_save.connect(create_employee_profile, sender=User)

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

    def test_duration_formatted_returns_readable_string(self):
        # Para evitar problema de precisión temporal:
        now = timezone.now()
        """Verifica que duration_formatted() retorna formato legible"""
        attendance = Attendance.objects.create(
            employee=self.employee,
            check_in=now - timedelta(hours=8, minutes=30),
            check_out=now,
        )

        formatted = attendance.duration_formatted()

        # Debe retornar algo como "8h 30m"
        self.assertIn("8h", formatted)
        self.assertIn("30m", formatted)

    def test_is_overtime_returns_true_for_9_hours(self):
        # Para evitar problema de precisión temporal:
        now = timezone.now()
        """Verifica que is_overtime() detecta horas extras (>8h)"""
        attendance = Attendance.objects.create(
            employee=self.employee, check_in=now - timedelta(hours=9), check_out=now
        )

        self.assertTrue(attendance.is_overtime())

    def test_is_overtime_returns_false_for_8_hours(self):
        # Para evitar problema de precisión temporal:
        now = timezone.now()
        """Verifica que is_overtime() retorna False para 8 horas exactas"""
        attendance = Attendance.objects.create(
            employee=self.employee, check_in=now - timedelta(hours=8), check_out=now
        )

        self.assertFalse(attendance.is_overtime())

    def test_is_overtime_returns_false_for_7_hours(self):
        # Para evitar problema de precisión temporal:
        now = timezone.now()
        """Verifica que is_overtime() retorna False para menos de 8 horas"""
        attendance = Attendance.objects.create(
            employee=self.employee, check_in=now - timedelta(hours=7), check_out=now
        )

        self.assertFalse(attendance.is_overtime())

    def test_is_overtime_returns_false_without_checkout(self):
        # Para evitar problema de precisión temporal:
        now = timezone.now()
        """Verifica que is_overtime() retorna False sin check_out"""
        attendance = Attendance.objects.create(
            employee=self.employee, check_in=now - timedelta(hours=10)
        )

        # Sin check_out, no hay horas extras confirmadas
        self.assertFalse(attendance.is_overtime())

    def test_is_overtime_with_custom_standard_hours(self):
        # Para evitar problema de precisión temporal:
        now = timezone.now()
        """Verifica que is_overtime() acepta horas estándar personalizadas"""
        attendance = Attendance.objects.create(
            employee=self.employee, check_in=now - timedelta(hours=7), check_out=now
        )

        # 7 horas es overtime si el estándar es 6
        self.assertTrue(attendance.is_overtime(standard_hours=6))
        # 7 horas NO es overtime si el estándar es 8
        self.assertFalse(attendance.is_overtime(standard_hours=8))

    def test_status_defaults_to_present(self):
        """Verifica que el estado por defecto es 'present'"""
        attendance = Attendance.objects.create(
            employee=self.employee, check_in=timezone.now()
        )

        self.assertEqual(attendance.status, "present")

    def test_created_at_is_auto_set(self):
        """Verifica que created_at se establece automáticamente"""
        before = timezone.now()

        attendance = Attendance.objects.create(
            employee=self.employee, check_in=timezone.now()
        )

        after = timezone.now()

        self.assertGreaterEqual(attendance.created_at, before)
        self.assertLessEqual(attendance.created_at, after)


class AttendanceQueryTest(TestCase):
    """Tests para consultas comunes de Attendance"""

    """Como en el modelo Employee tengo que se cree automáticamente un empleado tras crearse un user con un post_save, voy a desactivar esta función para los tests"""

    @classmethod
    def setUpClass(cls):
        """Desactivar señales antes de ejecutar los tests"""
        super().setUpClass()
        # Desconectar la señal post_save
        from django.db.models.signals import post_save

        from apps.employees.models import create_employee_profile

        post_save.disconnect(create_employee_profile, sender=User)

    """Quiero que se vuelva a activar el post_save del modelo tras realizar los tests"""

    @classmethod
    def tearDownClass(cls):
        """Reconectar señales después de los tests"""
        super().tearDownClass()
        # Reconectar la señal
        from django.db.models.signals import post_save

        from apps.employees.models import create_employee_profile

        post_save.connect(create_employee_profile, sender=User)

    def setUp(self):
        """Configuración inicial"""
        self.department = Department.objects.create(
            name="Limpieza", code="LIM", color="#10B981"
        )

        # Creación de 3 empleados
        self.employees = []
        for i in range(3):
            user = User.objects.create_user(
                username=f"employee{i}", password="testpass123"
            )
            employee = Employee.objects.create(
                user=user, department=self.department, role="camarero_piso"
            )
            self.employees.append(employee)

    def test_filter_attendances_by_date(self):
        """Verifica que se pueden filtrar asistencias por fecha"""
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        # Crear asistencias de hoy y ayer
        Attendance.objects.create(
            employee=self.employees[0],
            check_in=timezone.make_aware(
                timezone.datetime.combine(today, timezone.datetime.min.time())
            ),
        )
        Attendance.objects.create(
            employee=self.employees[1],
            check_in=timezone.make_aware(
                timezone.datetime.combine(yesterday, timezone.datetime.min.time())
            ),
        )

        # Filtrar solo las de hoy
        today_attendances = Attendance.objects.filter(check_in__date=today)

        self.assertEqual(today_attendances.count(), 1)

    def test_filter_active_attendances_without_checkout(self):
        """Verifica que se pueden filtrar asistencias activas (sin check_out)"""
        # Crear 2 con check_out y 1 sin check_out
        Attendance.objects.create(
            employee=self.employees[0],
            check_in=timezone.now() - timedelta(hours=8),
            check_out=timezone.now(),
        )
        Attendance.objects.create(
            employee=self.employees[1],
            check_in=timezone.now() - timedelta(hours=5)
            # Sin check_out
        )

        active = Attendance.objects.filter(check_out__isnull=True)

        self.assertEqual(active.count(), 1)
        self.assertEqual(active.first().employee, self.employees[1])
