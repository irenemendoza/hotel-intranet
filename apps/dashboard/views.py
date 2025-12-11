# apps/dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from apps.rooms.models import Room, CleaningTask, MaintenanceRequest
from apps.tasks.models import Task
from apps.users.models import Department


@login_required
def home(request):
    """Dashboard principal con estadísticas"""
    user = request.user
    user_dept = user.profile.department
    
    # Estadísticas generales
    context = {
        'total_rooms': Room.objects.filter(is_active=True).count(),
        'clean_rooms': Room.objects.filter(status=Room.StatusChoices.CLEAN, is_active=True).count(),
        'dirty_rooms': Room.objects.filter(status=Room.StatusChoices.DIRTY, is_active=True).count(),
        'maintenance_rooms': Room.objects.filter(
            Q(status=Room.StatusChoices.MAINTENANCE) | Q(status=Room.StatusChoices.OUT_OF_ORDER), 
            is_active=True
        ).count(),
    }
    
    # Tareas pendientes del usuario
    context['my_pending_tasks'] = Task.objects.filter(
        assigned_to=user,
        status__in=[Task.StatusChoices.PENDING, Task.StatusChoices.IN_PROGRESS]
    ).order_by('due_date')[:5]
    
    # Tareas del departamento
    if user_dept:
        context['dept_tasks'] = Task.objects.filter(
            department=user_dept,
            status__in=[Task.StatusChoices.PENDING, Task.StatusChoices.IN_PROGRESS]
        ).order_by('-priority', 'due_date')[:5]
    
    # Estadísticas específicas por departamento
    if user_dept and user_dept.code == 'LIM':  # Limpieza
        context['pending_cleaning'] = CleaningTask.objects.filter(
            status__in=[CleaningTask.StatusChoices.PENDING, CleaningTask.StatusChoices.IN_PROGRESS]
        ).count()
        context['my_cleaning_tasks'] = CleaningTask.objects.filter(
            assigned_to=user,
            status__in=[CleaningTask.StatusChoices.PENDING, CleaningTask.StatusChoices.IN_PROGRESS]
        ).order_by('priority', 'scheduled_time')[:5]
    
    elif user_dept and user_dept.code == 'MAN':  # Mantenimiento
        context['pending_maintenance'] = MaintenanceRequest.objects.filter(
            status__in=[MaintenanceRequest.StatusChoices.PENDING, MaintenanceRequest.StatusChoices.ASSIGNED, MaintenanceRequest.StatusChoices.IN_PROGRESS]
        ).count()
        context['urgent_maintenance'] = MaintenanceRequest.objects.filter(
            priority=MaintenanceRequest.StatusChoices.URGENT,
            status__in=[MaintenanceRequest.StatusChoices.PENDING, MaintenanceRequest.StatusChoices.ASSIGNED]
        )[:5]
    
    elif user_dept and user_dept.code == 'REC':  # Recepción
        context['occupied_rooms'] = Room.objects.filter(occupancy=Room.StatusChoices.OCCUPIED).count()
        context['vacant_rooms'] = Room.objects.filter(occupancy=Room.StatusChoices.VACANT).count()
        context['reserved_rooms'] = Room.objects.filter(occupancy=Room.StatusChoices.RESERVED).count()
    
    # Actividad reciente
    today = timezone.now().date()
    context['recent_tasks'] = Task.objects.filter(
        created_at__date=today
    ).order_by('-created_at')[:5]
    
    return render(request, 'dashboard/home.html', context)