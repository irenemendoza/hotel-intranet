# apps/dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from apps.rooms.models import Room, CleaningTask, MaintenanceRequest
from apps.employees.models import Department


# apps/dashboard/views.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class HomeView(LoginRequiredMixin, TemplateView):
    """Dashboard principal que redirige según rol"""
    
    def get_template_names(self):
        if not hasattr(self.request.user, 'profile'):
            return ['dashboard/home.html']
        
        role = self.request.user.profile.role
        
        # Mapeo de roles a dashboards
        dashboard_map = {
            'director': 'dashboard/director.html',
            'jefe_recepcion': 'dashboard/jefe_recepcion.html',
            'jefe_limpieza': 'dashboard/jefe_limpieza.html',
            'camarero_piso': 'dashboard/camarero_piso.html',
            'mantenimiento': 'dashboard/mantenimiento.html',
            'rrhh': 'dashboard/rrhh.html',
        }
        
        return [dashboard_map.get(role, 'dashboard/home.html')]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self.request.user, 'profile'):
            profile = self.request.user.profile
            
            # Datos comunes
            context['profile'] = profile
            context['notifications_count'] = 5  # Ejemplo
            
            # Datos específicos por rol
            if profile.role == 'camarero_piso':
                from apps.rooms.models import CleaningTask
                context['pending_tasks'] = CleaningTask.objects.filter(
                    assigned_to=profile,
                    status='pending'
                ).count()
            
            elif profile.is_supervisor():
                context['team_size'] = profile.get_supervised_employees().count()
        
        return context


@login_required
def home(request):
    """Dashboard principal con estadísticas"""
    user = request.user

    try:
        user_dept = user.profile.department
    except:
        user_dept = None
        
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