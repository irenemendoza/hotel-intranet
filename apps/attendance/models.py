from django.db import models
from django.utils import timezone


class Attendance(models.Model):
    """Registro de fichaje de entrada y salida de empleados"""
    
    class StatusChoices(models.TextChoices):
        PRESENT = 'present', 'Presente'
        LATE = 'late', 'Tarde'
        ABSENT = 'absent', 'Ausente'
        HALF_DAY = 'half_day', 'Medio día'
    
    employee = models.ForeignKey(
        "employees.Employee",
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
