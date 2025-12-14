from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.validators import RegexValidator
from django.utils import timezone

class ColorChoices(models.TextChoices):
    AZUL = '#3B82F6', 'Azul'
    VERDE = '#10B981', 'Verde'
    AMARILLO = '#F59E0B', 'Amarillo'
    ROJO = '#EF4444', 'Rojo'
    PURPURA = '#8B5CF6', 'Púrpura'
    ROSA = '#EC4899', 'Rosa'
    NARANJA = '#F97316', 'Naranja'
    CYAN = '#06B6D4', 'Cyan'
    INDIGO = '#6366F1', 'Índigo'
    LIMA = '#84CC16', 'Lima'
    ESMERALDA = '#059669', 'Esmeralda'
    GRIS = '#6B7280', 'Gris'
    

class Department(models.Model):
    # Departamentos del hotel:
    name = models.CharField(
    'Nombre', 
    max_length=50,
    )
    color = models.CharField(
    'Color', 
    max_length=7,
    choices=ColorChoices.choices, 
    default=ColorChoices.AZUL)
    code = models.CharField(
    'Código', 
    max_length=3, 
    unique=True,
    validators=[
            RegexValidator(
                regex='^[A-Z]{3}$',
                message='El código debe tener exactamente 3 letras mayúsculas',
                code='invalid_code'
            )
        ],
        help_text='Código de 3 letras mayúsculas (ej: DIR, REC, LIM)'
    )
    description = models.TextField(
        'Descripción',
        blank=True
    )
    is_active = models.BooleanField(
        'Activo',
        default=True
        )
    created_at = models.DateTimeField(
        'Fecha de creación',
        auto_now_add=True
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.upper()
        super().save(*args, **kwargs)

class UserProfile(models.Model):
    # Perfil del usuario con información del hotel
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Departamento'
    )
    phone = models.CharField(
        'Teléfono',
        max_length=20,
        blank=True
    )
    position = models.CharField(
        'Cargo',
        max_length=100,
        blank=True
    )
    avatar = models.ImageField(
        'Avatar', 
        upload_to='avatars/', 
        blank=True, 
        null=True
        )
    employee_number = models.CharField(
        'Número de empleado', 
        max_length=20, 
        unique=True, 
        blank=True, 
        null=True
        )
    hire_date = models.DateField(
        'Fecha de contratación', 
        null=True, 
        blank=True)
    is_available = models.BooleanField(
        'Disponible', 
        default=True, 
        help_text='Indica si el empleado está disponible para asignaciones'
        )
    bio = models.TextField(
        'Biografía', 
        blank=True, 
        help_text='Información adicional del empleado'
        )
    created_at = models.DateTimeField(
        'Fecha de creación', 
        auto_now_add=True
        )
    updated_at = models.DateTimeField(
        'Última actualización', 
        auto_now=True
        )
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.department}"
    
    def get_full_name(self):
        return self.user.get_full_name() or self.user.username

    def get_current_attendance(self):
        """Obtiene el fichaje activo actual (sin check_out)"""
        return self.attendances.filter(check_out__isnull=True).first()
    
    def is_checked_in(self):
        """Verifica si el empleado está fichado actualmente"""
        return self.get_current_attendance() is not None
    
    def get_today_work_hours(self):
        """Calcula las horas trabajadas hoy"""
        today = timezone.now().date()
        attendances = self.attendances.filter(check_in__date=today)
        
        total_hours = timedelta()
        for attendance in attendances:
            if attendance.check_out:
                total_hours += attendance.duration()
        
        return total_hours

class Attendance(models.Model):
    """Registro de fichaje de entrada y salida de empleados"""
    
    class StatusChoices(models.TextChoices):
        PRESENT = 'present', 'Presente'
        LATE = 'late', 'Tarde'
        ABSENT = 'absent', 'Ausente'
        HALF_DAY = 'half_day', 'Medio día'
    
    employee = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='Empleado'
    )
    check_in = models.DateTimeField(
        'Hora de entrada',
        default=timezone.now
    )
    check_out = models.DateTimeField(
        'Hora de salida',
        null=True,
        blank=True
    )
    status = models.CharField(
        'Estado',
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PRESENT
    )
    notes = models.TextField(
        'Notas',
        blank=True,
        help_text='Observaciones sobre el fichaje'
    )
    check_in_location = models.CharField(
        'Ubicación entrada',
        max_length=200,
        blank=True,
        help_text='Ubicación GPS o lugar de fichaje'
    )
    check_out_location = models.CharField(
        'Ubicación salida',
        max_length=200,
        blank=True
    )
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'
        ordering = ['-check_in']
        indexes = [
            models.Index(fields=['employee', '-check_in']),
            models.Index(fields=['check_in']),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.check_in.strftime('%d/%m/%Y %H:%M')}"
    
    def duration(self):
        """Calcula la duración del turno"""
        if self.check_out:
            return self.check_out - self.check_in
        return timezone.now() - self.check_in
    
    def duration_formatted(self):
        """Retorna la duración en formato legible"""
        duration = self.duration()
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        return f"{hours}h {minutes}m"
    
    def is_overtime(self, standard_hours=8):
        """Verifica si hay horas extras (más de 8 horas)"""
        if self.check_out:
            hours = self.duration().total_seconds() / 3600
            return hours > standard_hours
        return False


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
        UserProfile,
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

# Signals para crear perfil automáticamente
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()