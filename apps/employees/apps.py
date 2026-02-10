from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.employees"

    def ready(self):
        # Import signals when Django starts
        import apps.employees.signals
