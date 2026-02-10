from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Employee


@receiver(post_save, sender=User)
def create_employee_profile(sender, instance, created, **kwargs):
    # Creates an Employee when a User is created
    if created:
        # Only create if it doesn't exist
        if not hasattr(instance, "employee"):
            Employee.objects.create(
                user=instance,
                # Don't assign role automatically, must be done manually
            )


@receiver(post_save, sender=User)
def save_employee_profile(sender, instance, **kwargs):
    # Saves the Employee when the User is saved
    if hasattr(instance, "employee"):
        instance.employee.save(update_fields=["updated_at"])
