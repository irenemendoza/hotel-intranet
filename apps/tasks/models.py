# apps/tasks/models.py
from django.db import models
from django.contrib.auth.models import User
from apps.users.models import Department

class Task(models.Model):
    """Tareas generales del hotel (no específicas de limpieza)"""
    class PriorityChoices(models.TextChoices):
        LOW = 'low', 'Baja'
        MEDIUM = 'medium', 'Media'
        HIGH = 'high', 'Alta'
        URGENT = 'urgent', 'Urgente'
    
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        IN_PROGRESS = 'in_progress', 'En progreso'
        COMPLETED = 'completed', 'Completada'
        CANCELLED = 'cancelled', 'Cancelada'
    
    
    title = models.CharField(
        'Título', 
        max_length=200
        )
    description = models.TextField(
        'Descripción'
        )
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        verbose_name='Departamento'
        )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_tasks',
        verbose_name='Creado por'
        )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_tasks',
        verbose_name='Asignado a'
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
    due_date = models.DateTimeField(
        'Fecha límite', 
        null=True, 
        blank=True
        )
    completed_at = models.DateTimeField(
        'Fecha de completado', 
        null=True, 
        blank=True
        )
    attachments = models.FileField(
        'Archivos adjuntos', 
        upload_to='tasks/', 
        blank=True, 
        null=True
        )
    notes = models.TextField(
        'Notas adicionales', 
        blank=True
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
        return f"{self.title} - {self.department}"
    
    def is_overdue(self):
        """Verifica si la tarea está vencida"""
        from django.utils import timezone
        if self.due_date and self.status != self.StatusChoices.COMPLETED:
            return timezone.now() > self.due_date
        return False
    
    def get_priority_color(self):
        """Retorna un color según la prioridad"""
        colors = {
            self.PriorityChoices.LOW: 'info',
            self.PriorityChoices.MEDIUM: 'warning',
            self.PriorityChoices.HIGH: 'danger',
            self.PriorityChoices.URGENT: 'dark',
        }
        return colors.get(self.priority, 'secondary')
   

class TaskComment(models.Model):
    """Comentarios en las tareas"""
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name='Tarea')
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='Usuario'
        )
    comment = models.TextField(
        'Comentario'
        )
    created_at = models.DateTimeField(
        'Fecha de creación', 
        auto_now_add=True
        )
    
    
    def __str__(self):
        return f"Comentario de {self.user.username} en {self.task.title}"