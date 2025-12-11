# apps/rooms/models.py
from django.db import models
from django.contrib.auth.models import User
    
  
class RoomType(models.Model):
    """Tipos de habitación (Individual, Doble, Suite, etc.)"""
    name = models.CharField(
        'Nombre', 
        max_length=50
        )
    code = models.CharField(
        'Código', 
        max_length=10, 
        unique=True
        )
    capacity = models.PositiveIntegerField(
        'Capacidad', 
        help_text='Número máximo de huéspedes'
        )
    base_price = models.DecimalField(
        'Precio base', 
        max_digits=10, 
        decimal_places=2
        )
    description = models.TextField(
        'Descripción', 
        blank=True
        )
    amenities = models.TextField(
        'Comodidades', 
        blank=True, 
        help_text='Lista de amenidades incluidas'
        )
    is_active = models.BooleanField(
        'Activo', 
        default=True
        )
   
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Room(models.Model):

    class StatusChoices(models.TextChoices):
        CLEAN = 'clean', 'Limpia'
        DIRTY = 'dirty', 'Sucia'
        INSPECTED = 'inspected', 'Inspeccionada'
        MAINTENANCE = 'maintenance', 'En mantenimiento'
        OUT_OF_ORDER = 'out_of_order', 'Fuera de servicio'
    

    class OccupancyChoices(models.TextChoices):
        VACANT = 'vacant', 'Vacante'
        OCCUPIED = 'occupied', 'Ocupada'
        RESERVED = 'reserved', 'Reservada'
    
    
    number = models.CharField(
        'Número', 
        max_length=10, 
        unique=True
        )
    floor = models.PositiveIntegerField(
        'Piso'
        )
    room_type = models.ForeignKey(
        RoomType, 
        on_delete=models.PROTECT,
        verbose_name='Tipo de habitación'
        )
    status = models.CharField(
        'Estado de limpieza', 
        max_length=20, 
        choices=StatusChoices.choices, 
        default=StatusChoices.DIRTY
        )
    occupancy = models.CharField(
        'Estado de ocupación', 
        max_length=20, 
        choices=OccupancyChoices.choices, 
        default=OccupancyChoices.VACANT
        )
    last_cleaned = models.DateTimeField(
        'Última limpieza', 
        null=True, 
        blank=True
        )
    last_inspected = models.DateTimeField(
        'Última inspección', 
        null=True, 
        blank=True
        )
    notes = models.TextField(
        'Notas', 
        blank=True
        )
    is_active = models.BooleanField(
        'Activa', 
        default=True
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
        return f"Habitación {self.number} - Piso {self.floor}"
    
    def get_status_display_color(self):
        """Retorna un color según el estado"""
        colors = {
            self.CLEAN: 'success',
            self.DIRTY: 'warning',
            self.INSPECTED: 'info',
            self.MAINTENANCE: 'danger',
            self.OUT_OF_ORDER: 'dark',
        }
        return colors.get(self.status, 'secondary')

class CleaningTask(models.Model):
    """Tareas de limpieza asignadas a habitaciones"""
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        IN_PROGRESS = 'in_progress', 'En progreso'
        COMPLETED = 'completed', 'Completada'
        VERIFIED = 'verified', 'Verificada'
    
      
    # Tipos de limpieza
    class TypeChoices(models.TextChoices):
        CHECKOUT = 'checkout', 'Salida'
        STAY_OVER = 'stay_over', 'Estadía'
        DEEP_CLEANING = 'deep_cleaning', 'Limpieza profunda'
    
    
    room = models.ForeignKey(
        Room, 
        on_delete=models.CASCADE, 
        related_name='cleaning_tasks', 
        verbose_name='Habitación'
        )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='cleaning_tasks',
        verbose_name='Asignado a'
        )
    cleaning_type = models.CharField(
        'Tipo de limpieza', 
        max_length=20, 
        choices=TypeChoices.choices, 
        default=TypeChoices.CHECKOUT
        )
    status = models.CharField(
        'Estado', 
        max_length=20, 
        choices=StatusChoices.choices, 
        default=StatusChoices.PENDING
        )
    priority = models.PositiveIntegerField(
        'Prioridad', 
        default=1, 
        help_text='1 = Alta, 5 = Baja'
        )
    scheduled_time = models.DateTimeField(
        'Hora programada'
        )
    started_at = models.DateTimeField(
        'Hora de inicio', 
        null=True, 
        blank=True
        )
    completed_at = models.DateTimeField(
        'Hora de finalización', 
        null=True, 
        blank=True
        )
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='verified_cleanings',
        verbose_name='Verificado por',
        )
    verified_at = models.DateTimeField(
        'Fecha de verificación', 
        null=True, 
        blank=True
        )
    notes = models.TextField(
        'Notas', 
        blank=True
        )
    photos = models.ImageField(
        'Fotos', 
        upload_to='cleaning_tasks/', 
        blank=True, 
        null=True
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
        return f"{self.room} - {self.get_status_display()} ({self.scheduled_time.strftime('%d/%m/%Y %H:%M')})"
    
    def duration(self):
        """Calcula la duración de la limpieza"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class MaintenanceRequest(models.Model):
    """Solicitudes de mantenimiento para habitaciones"""
    class PriorityChoices(models.TextChoices):
        LOW = 'low', 'Baja'
        MEDIUM = 'medium', 'Media'
        HIGH = 'high', 'Alta'
        URGENT = 'urgent', 'Urgente'
    
    class StatusChoices(models.TextChoices):
    
        PENDING = 'pending', 'Pendiente'
        ASSIGNED = 'assigned', 'Asignada'
        IN_PROGRESS = 'in_progress', 'En progreso'
        COMPLETED = 'completed', 'Completada'
        CANCELLED = 'cancelled', 'Cancelada'
    
    
    
    room = models.ForeignKey(
        Room, 
        on_delete=models.CASCADE, 
        related_name='maintenance_requests',
        verbose_name='Habitación'
        )
    reported_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='reported_maintenance',
        verbose_name='Reportado por'
        )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_maintenance',
        verbose_name='Asignado a'
        )
    title = models.CharField(
        'Título', 
        max_length=200
        )
    description = models.TextField(
        'Descripción'
        )
    priority = models.CharField(
        'Prioridad', 
        max_length=10, 
        choices=PriorityChoices.choices, 
        default=PriorityChoices.MEDIUM
        )
    status = models.CharField(
        'Estado', 
        max_length=20, 
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
        )
    resolution = models.TextField(
        'Resolución', 
        blank=True
        )
    photos = models.ImageField(
        'Fotos', 
        upload_to='maintenance/', 
        blank=True, 
        null=True
        )
    created_at = models.DateTimeField(
        'Fecha de creación', 
        auto_now_add=True
        )
    assigned_at = models.DateTimeField(
        'Fecha de asignación', 
        null=True, 
        blank=True
        )
    started_at = models.DateTimeField(
        'Fecha de inicio', 
        null=True, 
        blank=True
        )
    resolved_at = models.DateTimeField(
        'Fecha de resolución', 
        null=True, 
        blank=True
        )
   
    
    def __str__(self):
        return f"{self.room} - {self.title} [{self.get_priority_display()}]"
    
    def get_priority_color(self):
        """Retorna un color según la prioridad"""
        colors = {
            self.LOW: 'info',
            self.MEDIUM: 'warning',
            self.HIGH: 'danger',
            self.URGENT: 'dark',
        }
        return colors.get(self.priority, 'secondary')