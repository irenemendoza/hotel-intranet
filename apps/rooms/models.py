# apps/rooms/models.py
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.employees.models import Employee

from decimal import Decimal
  
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
    
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        CONFIRMED = 'confirmed', 'Confirmada'
        PENDING_CHECKIN = 'pending_checkin', 'Checkin pendiente'
        CHECKED_IN = 'checked_in', 'En estancia'
        PENDING_CHECKOUT = 'pending_checkout', 'Checkout pendiente'
        CHECKED_OUT = 'checked_out', 'Finalizada'
        CANCELLED = 'cancelled', 'Cancelada'
        NO_SHOW = 'no_show', 'No se presentó'
    
    class PaymentStatusChoices(models.TextChoices):
        UNPAID = 'unpaid', 'Sin pagar'
        PARTIAL = 'partial', 'Pago parcial'
        PAID = 'paid', 'Pagado'
        REFUNDED = 'refunded', 'Reembolsado'
    
    # Información de la reserva
    reservation_number = models.CharField(
        'Número de reserva',
        max_length=20,
        unique=True,
        editable=False,
        help_text='Se genera automáticamente'
    )
    room = models.ForeignKey(
        'Room',
        on_delete=models.PROTECT,
        related_name='reservations',
        verbose_name='Habitación'
    )
    
    # Fechas
    check_in_date = models.DateField('Fecha de entrada')
    check_out_date = models.DateField('Fecha de salida')
    actual_check_in = models.DateTimeField(
        'Check-in real',
        null=True,
        blank=True,
        help_text='Fecha y hora real de entrada'
    )
    actual_check_out = models.DateTimeField(
        'Check-out real',
        null=True,
        blank=True,
        help_text='Fecha y hora real de salida'
    )
    
    # Información del huésped
    guest_first_name = models.CharField('Nombre', max_length=100)
    guest_last_name = models.CharField('Apellidos', max_length=100)
    guest_email = models.EmailField(
        'Email',
        validators=[EmailValidator()],
        help_text='Email del huésped'
    )
    guest_phone = models.CharField('Teléfono', max_length=20)
    guest_dni = models.CharField(
        'DNI/Pasaporte',
        max_length=20,
        blank=True,
        help_text='Documento de identidad'
    )
    guest_nationality = models.CharField(
        'Nacionalidad',
        max_length=50,
        blank=True
    )
    guest_address = models.TextField(
        'Dirección',
        blank=True
    )
    
    # Detalles de la reserva
    adults = models.PositiveIntegerField(
        'Adultos',
        default=1,
        validators=[MinValueValidator(1)]
    )
    children = models.PositiveIntegerField(
        'Niños',
        default=0,
        validators=[MinValueValidator(0)]
    )
    special_requests = models.TextField(
        'Solicitudes especiales',
        blank=True,
        help_text='Peticiones del huésped'
    )
    
    # Estado y gestión
    status = models.CharField(
        'Estado',
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_reservations',
        verbose_name='Creado por'
    )
    checked_in_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkins_processed',
        verbose_name='Check-in realizado por'
    )
    checked_out_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkouts_processed',
        verbose_name='Check-out realizado por'
    )
    
    # Información financiera
    room_rate = models.DecimalField(
        'Tarifa por noche',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    total_amount = models.DecimalField(
        'Importe total',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    paid_amount = models.DecimalField(
        'Importe pagado',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    payment_status = models.CharField(
        'Estado del pago',
        max_length=20,
        choices=PaymentStatusChoices.choices,
        default=PaymentStatusChoices.UNPAID
    )
    
    # Notas internas
    internal_notes = models.TextField(
        'Notas internas',
        blank=True,
        help_text='Notas del personal (no visibles para el huésped)'
    )
    cancellation_reason = models.TextField(
        'Motivo de cancelación',
        blank=True
    )
    
    # Metadatos
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última actualización', auto_now=True)
    
    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-check_in_date', '-created_at']
        indexes = [
            models.Index(fields=['check_in_date', 'check_out_date']),
            models.Index(fields=['room', 'status']),
            models.Index(fields=['guest_email']),
            models.Index(fields=['reservation_number']),
        ]
    
    def __str__(self):
        return f"{self.reservation_number} - {self.guest_full_name} - Hab. {self.room.number}"
    
    def save(self, *args, **kwargs):
        # Generar número de reserva si no existe
        if not self.reservation_number:
            self.reservation_number = self.generate_reservation_number()
        
        # Calcular importe total automáticamente
        if not self.total_amount or self.total_amount == 0:
            self.total_amount = self.calculate_total()
        
        # Actualizar estado de pago
        self.update_payment_status()
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validaciones del modelo"""
        super().clean()
        
        # Validar fechas
        if self.check_in_date and self.check_out_date:
            if self.check_out_date <= self.check_in_date:
                raise ValidationError({
                    'check_out_date': 'La fecha de salida debe ser posterior a la fecha de entrada'
                })
        
        # Validar capacidad de la habitación
        if self.room:
            total_guests = self.adults + self.children
            if total_guests > self.room.room_type.capacity:
                raise ValidationError({
                    'adults': f'Esta habitación tiene capacidad máxima de {self.room.room_type.capacity} personas'
                })
        
        # Validar disponibilidad de la habitación
        if self.room and self.check_in_date and self.check_out_date:
            if not self.is_room_available():
                raise ValidationError({
                    'room': 'Esta habitación no está disponible para las fechas seleccionadas'
                })
    
    # Propiedades calculadas
    @property
    def guest_full_name(self):
        """Nombre completo del huésped"""
        return f"{self.guest_first_name} {self.guest_last_name}"
    
    @property
    def nights(self):
        """Número de noches de la reserva"""
        if self.check_in_date and self.check_out_date:
            return (self.check_out_date - self.check_in_date).days
        return 0
    
    @property
    def is_active(self):
        """Verifica si la reserva está activa (en estancia)"""
        return self.status == self.StatusChoices.CHECKED_IN
    
    @property
    def is_confirmed(self):
        """Verifica si la reserva está confirmada"""
        return self.status == self.StatusChoices.CONFIRMED
    
    @property
    def is_completed(self):
        """Verifica si la reserva está completada"""
        return self.status == self.StatusChoices.CHECKED_OUT
    
    @property
    def pending_amount(self):
        """Importe pendiente de pago"""
        return self.total_amount - self.paid_amount
    
    @property
    def is_paid(self):
        """Verifica si está totalmente pagado"""
        return self.paid_amount >= self.total_amount
    
    def nights_stayed(self):
        """Calcula cuántas noches lleva el huésped"""
        if self.actual_check_in:
            if self.actual_check_out:
                delta = self.actual_check_out - self.actual_check_in
            else:
                delta = timezone.now() - self.actual_check_in
            return delta.days
        return 0
    
    def needs_linen_change(self):
        """Determina si necesita cambio de sábanas (cada 3 días)"""
        return self.nights_stayed() >= 3
    
    def get_cleaning_type_needed(self):
        """Determina qué tipo de limpieza necesita"""
        if not self.is_active:
            return None
        
        today = timezone.now().date()
        
        # Departure (salida)
        if self.check_out_date == today:
            return 'checkout'
        # Stay over con cambio de sábanas
        elif self.needs_linen_change():
            return 'deep_cleaning'
        # Stay over normal
        else:
            return 'stay_over'
    
    # Métodos de negocio
    def calculate_total(self):
        """Calcula el importe total de la reserva"""
        return self.room_rate * self.nights
    
    def update_payment_status(self):
        """Actualiza el estado del pago según el importe pagado"""
        if self.paid_amount >= self.total_amount:
            self.payment_status = self.PaymentStatusChoices.PAID
        elif self.paid_amount > 0:
            self.payment_status = self.PaymentStatusChoices.PARTIAL
        else:
            self.payment_status = self.PaymentStatusChoices.UNPAID
    
    def generate_reservation_number(self):
        """Genera un número único de reserva"""
        from django.utils.crypto import get_random_string
        from datetime import datetime
        
        # Formato: RES-YYYYMMDD-XXXX
        date_str = datetime.now().strftime('%Y%m%d')
        random_str = get_random_string(length=4, allowed_chars='0123456789')
        
        reservation_number = f"RES-{date_str}-{random_str}"
        
        # Verificar que no exista
        while Reservation.objects.filter(reservation_number=reservation_number).exists():
            random_str = get_random_string(length=4, allowed_chars='0123456789')
            reservation_number = f"RES-{date_str}-{random_str}"
        
        return reservation_number
    
    def is_room_available(self):
        """Verifica si la habitación está disponible para las fechas seleccionadas"""
        # Excluir esta misma reserva si estamos editando
        queryset = Reservation.objects.filter(room=self.room)
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)
        
        # Buscar reservas que se solapen
        overlapping = queryset.filter(
            check_in_date__lt=self.check_out_date,
            check_out_date__gt=self.check_in_date,
            status__in=[
                self.StatusChoices.CONFIRMED,
                self.StatusChoices.CHECKED_IN
            ]
        )
        
        return not overlapping.exists()
    
    def check_in(self, employee):
        """Procesa el check-in"""
        if self.status != self.StatusChoices.CONFIRMED:
            raise ValidationError('Solo se puede hacer check-in de reservas confirmadas')
        
        self.status = self.StatusChoices.CHECKED_IN
        self.actual_check_in = timezone.now()
        self.checked_in_by = employee
        
        # Actualizar estado de la habitación
        self.room.status = Room.StatusChoices.OCCUPIED
        self.room.occupancy = Room.OccupancyChoices.OCCUPIED
        self.room.save()
        
        self.save()
    
    def check_out(self, employee):
        """Procesa el check-out"""
        if self.status != self.StatusChoices.CHECKED_IN:
            raise ValidationError('Solo se puede hacer check-out de reservas con check-in realizado')
        
        self.status = self.StatusChoices.CHECKED_OUT
        self.actual_check_out = timezone.now()
        self.checked_out_by = employee
        
        # Actualizar estado de la habitación
        self.room.status = Room.StatusChoices.DIRTY
        self.room.occupancy = Room.OccupancyChoices.VACANT
        self.room.save()
        
        # Crear tarea de limpieza automáticamente
        from apps.rooms.models import CleaningTask
        CleaningTask.objects.create(
            room=self.room,
            cleaning_type=CleaningTask.TypeChoices.CHECKOUT,
            priority=1,
            notes=f'Limpieza después de check-out - Reserva {self.reservation_number}'
        )
        
        self.save()
    
    def cancel(self, reason=''):
        """Cancela la reserva"""
        if self.status == self.StatusChoices.CHECKED_IN:
            raise ValidationError('No se puede cancelar una reserva con check-in realizado')
        
        self.status = self.StatusChoices.CANCELLED
        self.cancellation_reason = reason
        
        # Liberar la habitación
        if self.room.occupancy == Room.OccupancyChoices.RESERVED:
            self.room.occupancy = Room.OccupancyChoices.VACANT
            self.room.save()
        
        self.save()
    
    @property
    def pending_amount_display(self):
        return self.total_amount - self.amount_paid
    
    def get_status_color(self):
        """Retorna el color bootstrap según el estado"""
        colors = {
            self.StatusChoices.PENDING: 'secondary',
            self.StatusChoices.CONFIRMED: 'primary',
            self.StatusChoices.CHECKED_IN: 'success',
            self.StatusChoices.CHECKED_OUT: 'info',
            self.StatusChoices.CANCELLED: 'danger',
            self.StatusChoices.NO_SHOW: 'warning',
        }
        return colors.get(self.status, 'secondary')
    
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
    
    def get_current_reservation(self):
        """Obtiene la reserva activa actual"""
        return self.reservations.filter(
            status=Reservation.StatusChoices.CHECKED_IN,
            actual_check_in__isnull=False,
            actual_check_out__isnull=True
        ).first()
    
    def is_occupied(self):
        """Verifica si la habitación está ocupada"""
        return self.get_current_reservation() is not None
    
    def get_next_reservation(self):
        """Obtiene la próxima reserva confirmada"""
        today = timezone.now().date()
        return self.reservations.filter(
            status=Reservation.StatusChoices.CONFIRMED,
            check_in_date__gte=today
        ).order_by('check_in_date').first()

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
        Employee, 
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
    completed_at = models.DateTimeField(
        'Limpieza terminada', 
        auto_now=True
        )
    
    
    def __str__(self):
        return f"{self.room} - {self.get_status_display()}"
    
   

class MaintenanceTask(models.Model):
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
        Employee, 
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