from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta


   

class Department(models.Model):

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

class Employee(models.Model):
        
    class RoleChoices(models.TextChoices):
        # Dirección
        DIRECTOR = 'director', 'Director/a'
        
        # Recepción
        JEFE_RECEPCION = 'jefe_recepcion', 'Jefe/a de Recepción'
        RECEPCIONISTA = 'recepcionista', 'Recepcionista'
        
        # Limpieza
        JEFE_LIMPIEZA = 'jefe_limpieza', 'Jefe/a de Limpieza'
        CAMARERO_PISO = 'camarero_piso', 'Camarero/a de Piso'
        
        # Mantenimiento
        JEFE_MANTENIMIENTO = 'jefe_mantenimiento', 'Jefe/a de Mantenimiento'
        MANTENIMIENTO = 'mantenimiento', 'Personal de Mantenimiento'
        
        # RRHH
        RRHH = 'rrhh', 'Recursos Humanos'
    
    # ... campos existentes ...
    
    # Perfil del usuario con información del hotel
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Departamento'
    )
    role = models.CharField(
        'Rol',
        max_length=30,
        choices=RoleChoices.choices,
        help_text='Rol del empleado en el hotel'
    )
    phone = models.CharField(
        'Teléfono',
        max_length=20,
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
    
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.assign_to_group()
    
    def assign_to_group(self):
        """Asigna el usuario al grupo correspondiente según su rol"""
        from django.contrib.auth.models import Group
        
        # Mapeo de roles a grupos
        role_group_map = {
            'director': ['Dirección', 'Supervisores'],
            'jefe_recepcion': ['Recepción', 'Supervisores'],
            'recepcionista': ['Recepción'],
            'jefe_limpieza': ['Limpieza', 'Supervisores'],
            'camarero_piso': ['Limpieza'],
            'jefe_mantenimiento': ['Mantenimiento', 'Supervisores'],
            'mantenimiento': ['Mantenimiento'],
            'rrhh': ['RRHH', 'Supervisores'],
        }
        
        groups = role_group_map.get(self.role, [])
        self.user.groups.clear()
        
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            self.user.groups.add(group)
    
    def is_supervisor(self):
        """Verifica si el usuario es un supervisor/jefe"""
        return self.role in [
            'director', 'jefe_recepcion', 'jefe_limpieza', 
            'jefe_mantenimiento', 'rrhh'
        ]
    
    def can_manage_team(self):
        """Verifica si puede gestionar su equipo"""
        return self.is_supervisor()
    
    def get_supervised_employees(self):
        """Obtiene los empleados bajo su supervisión"""
        if not self.can_manage_team():
            return Employee.objects.none()
        
        # Mapeo de jefes a sus subordinados
        supervision_map = {
            'director': Employee.objects.all(),  # Ve todos
            'jefe_recepcion': Employee.objects.filter(role='recepcionista'),
            'jefe_limpieza': Employee.objects.filter(role='camarero_piso'),
            'jefe_mantenimiento': Employee.objects.filter(role='mantenimiento'),
            'rrhh': Employee.objects.all(),  # RRHH ve todos
        }
        
        return supervision_map.get(self.role, Employee.objects.none())
    
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

@receiver(post_save, sender=User)
def create_employee_profile(sender, instance, created, **kwargs):
    """Crea un Employee cuando se crea un User"""
    if created:
        # Solo crear si no existe
        if not hasattr(instance, 'employee'):
            Employee.objects.create(
                user=instance,
                # No asignar rol automáticamente, 
                # debe hacerse manualmente
            )

@receiver(post_save, sender=User)
def save_employee_profile(sender, instance, **kwargs):
    """Guarda el Employee cuando se guarda el User"""
    if hasattr(instance, 'employee'):
        instance.employee.save()

