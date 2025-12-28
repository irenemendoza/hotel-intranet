from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from apps.employees.models import Employee

class Leave(models.Model):
    """Gestión de permisos y vacaciones"""
    
    class LeaveTypeChoices(models.TextChoices):
        VACATION = 'vacation', 'Vacaciones'
        SICK = 'sick', 'Baja médica'
        PERSONAL = 'personal', 'Asunto personal'
        UNPAID = 'unpaid', 'Sin sueldo'
        OTHER = 'other', 'Otro'
    
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        APPROVED = 'approved', 'Aprobado'
        REJECTED = 'rejected', 'Rechazado'
        CANCELLED = 'cancelled', 'Cancelado'
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leaves',
        verbose_name='Empleado'
    )
    leave_type = models.CharField(
        'Tipo de permiso',
        max_length=20,
        choices=LeaveTypeChoices.choices
    )
    start_date = models.DateField('Fecha de inicio')
    end_date = models.DateField('Fecha de fin')
    reason = models.TextField('Motivo')
    status = models.CharField(
        'Estado',
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves',
        verbose_name='Aprobado por'
    )
    approved_at = models.DateTimeField('Fecha de aprobación', null=True, blank=True)
    rejection_reason = models.TextField('Motivo de rechazo', blank=True)
    attachment = models.FileField(
        'Documento adjunto',
        upload_to='leaves/',
        blank=True,
        null=True,
        help_text='Justificante médico u otro documento'
    )
    created_at = models.DateTimeField('Fecha de solicitud', auto_now_add=True)
    updated_at = models.DateTimeField('Última actualización', auto_now=True)
    
    class Meta:
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_leave_type_display()} ({self.start_date} - {self.end_date})"
    
    def duration_days(self):
        """Calcula la duración en días"""
        return (self.end_date - self.start_date).days + 1

