from django.db import models
from django.contrib.auth.models import User


class DepartmentChoices(models.TextChoices):
    DIRECCION = 'DIR', 'Dirección'
    RECEPCION = 'REC', 'Recepción'
    LIMPIEZA = 'LIM', 'Limpieza'
    MANTENIMIENTO = 'MAN', 'Mantenimiento'
    RESTAURANTE = 'RES', 'Restaurante'

class ColorChoices(models.TextChoices):
    AZUL = '#3B82F6', 'Azul'
    VERDE = '#10B981', 'Verde'
    AMARILLO = '#F59E0B', 'Amarillo'
    ROJO = '#EF4444', 'Rojo'
    PURPURA = '#8B5CF6', 'Púrpura'
    

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
    choices=DepartmentChoices.choices,
    unique=True
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
