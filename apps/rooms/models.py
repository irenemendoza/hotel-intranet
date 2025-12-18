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


class Reservation(models.Model):
    """Reservas de habitaciones"""
    room = models.ForeignKey(
        'Room', 
        on_delete=models.CASCADE, 
        related_name='reservations'
        )
    guest_name = models.CharField(
        'Nombre del huésped', 
        max_length=200,
        null=True, 
        blank=True
        )
    check_in = models.DateField(
        'Fecha de entrada'
        )
    check_out = models.DateField(
        'Fecha de salida'
        )
    actual_check_in = models.DateTimeField(
        'Check-in real', 
        null=True, 
        blank=True
        )
    actual_check_out = models.DateTimeField(
        'Check-out real', 
        null=True, 
        blank=True
        )
    nights = models.PositiveIntegerField(
        'Noches'
        )
    status = models.CharField(
        max_length=20, 
        choices=[
        ('confirmed', 'Confirmada'),
        ('checked_in', 'En estancia'),
        ('checked_out', 'Finalizada'),
        ('cancelled', 'Cancelada'),
        ], 
        default='confirmed')
    
    def is_active(self):
        return self.status == 'checked_in'

    def get_current_reservation(self):
        """Obtiene la reserva activa actual"""
        from django.utils import timezone
        return self.reservations.filter(
            status='checked_in',
            actual_check_in__isnull=False,
            actual_check_out__isnull=True
        ).first()

    def nights_stayed(self):
        """Calcula cuántas noches lleva el huésped"""
        reservation = self.get_current_reservation()
        if reservation and reservation.actual_check_in:
            from django.utils import timezone
            delta = timezone.now() - reservation.actual_check_in
            return delta.days
        return 0

    def needs_linen_change(self):
        """Determina si necesita cambio de sábanas (cada 3 días)"""
        return self.nights_stayed() >= 3

    def get_cleaning_type_needed(self):
        """Determina qué tipo de limpieza necesita"""
        reservation = self.get_current_reservation()
        if not reservation:
            return None
    
        from django.utils import timezone
        today = timezone.now().date()
    
        # Departure (salida)
        if reservation.check_out == today:
            return 'checkout'
        # Stay over con cambio de sábanas
        elif self.needs_linen_change():
            return 'deep_cleaning'
        # Stay over normal
        else:
            return 'stay_over'

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
            self.StatusChoices.CLEAN: 'success',
            self.StatusChoices.DIRTY: 'warning',
            self.StatusChoices.INSPECTED: 'info',
            self.StatusChoices.MAINTENANCE: 'danger',
            self.StatusChoices.OUT_OF_ORDER: 'dark',
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
        STAY_OVER = 'stay_over', 'Cliente'
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
        return f"{self.room} - {self.get_status_display()}"
    
   

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
    updated_at = models.DateTimeField(
        'Última actualización', 
        auto_now=True
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
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Solicitud de Mantenimiento'
        verbose_name_plural = 'Solicitudes de Mantenimiento'
    
    def __str__(self):
        return f"{self.room} - {self.title} [{self.get_priority_display()}]"
    
    def get_priority_color(self):
        """Retorna un color según la prioridad"""
        colors = {
            self.PriorityChoices.LOW: 'info',
            self.PriorityChoices.MEDIUM: 'warning',
            self.PriorityChoices.HIGH: 'danger',
            self.PriorityChoices.URGENT: 'dark',
        }
        return colors.get(self.priority, 'secondary')