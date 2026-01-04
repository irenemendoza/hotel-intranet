# apps/dashboard/views.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta


from apps.employees.models import Employee, Department
from apps.attendance.models import Attendance
from apps.leave.models import Leave
from apps.rooms.models import Room, Reservation, CleaningTask, MaintenanceTask



class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal que se adapta al rol del usuario"""
    
    def get_template_names(self):
        """Selecciona el template según el rol del usuario"""
        if not hasattr(self.request.user, 'employee'):
            return ['dashboard/home.html']
        
        role = self.request.user.employee.role
        
        template_map = {
            'director': 'dashboard/director.html',
            'jefe_recepcion': 'dashboard/jefe_recepcion.html',
            'recepcionista': 'dashboard/recepcionista.html',
            'jefe_limpieza': 'dashboard/jefe_limpieza.html',
            'camarero_piso': 'dashboard/camarero_piso.html',
            'jefe_mantenimiento': 'dashboard/jefe_mantenimiento.html',
            'mantenimiento': 'dashboard/mantenimiento.html',
            'rrhh': 'dashboard/rrhh.html',
        }
        
        template = template_map.get(role, 'dashboard/home.html')

        print(f"DEBUG: Usuario: {self.request.user.username}")
        print(f"DEBUG: Rol: {role}")
        print(f"DEBUG: Template a usar: {template}")

        return [template]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.request.user.employee
        today = timezone.now().date()
        
        # Datos comunes para todos
        context['employee'] = employee
        context['today'] = today
        context['greeting'] = self.get_greeting()
        
        # Datos específicos por rol
        role_context_methods = {
            'director': self.get_director_context,
            'jefe_recepcion': self.get_jefe_recepcion_context,
            'recepcionista': self.get_recepcionista_context,
            'jefe_limpieza': self.get_jefe_limpieza_context,
            'camarero_piso': self.get_camarero_piso_context,
            'jefe_mantenimiento': self.get_jefe_mantenimiento_context,
            'mantenimiento': self.get_mantenimiento_context,
            'rrhh': self.get_rrhh_context,
        }
        
        method = role_context_methods.get(employee.role)
        if method:
            context.update(method())
        
        return context
    
    def get_greeting(self):
        """Saludo según la hora del día"""
        hour = timezone.now().hour
        if hour < 12:
            return "Buenos días"
        elif hour < 20:
            return "Buenas tardes"
        else:
            return "Buenas noches"
    
    def _calculate_occupancy_rate(self):
        """Calcula el porcentaje de ocupación"""
        from apps.rooms.models import Room
        
        total = Room.objects.filter(is_active=True).count()
        occupied = Room.objects.filter(status='occupied').count()
        
        if total > 0:
            return round((occupied / total) * 100, 1)
        return 0
    
    # ==================== CONTEXTOS POR ROL ====================
    
    def get_director_context(self):
        """Dashboard para el Director"""
        today = timezone.now().date()
        
        return {
            # Estadísticas generales
            'total_employees': Employee.objects.filter(is_available=True).count(),
            'total_rooms': Room.objects.count(),
            'occupied_rooms': Room.objects.filter(status='occupied').count(),
            'available_rooms': Room.objects.filter(status='available').count(),
            
            # Asistencia hoy
            'employees_present': Attendance.objects.filter(
                check_in__date=today,
                check_out__isnull=True
            ).count(),
            
            # Permisos pendientes
            'pending_leaves': Leave.objects.filter(status='pending').count(),
            
            # Tareas pendientes
            'pending_cleaning': CleaningTask.objects.filter(
                status__in=['pending', 'in_progress']
            ).count(),
            'pending_maintenance': MaintenanceTask.objects.filter(
                status__in=['pending', 'in_progress']
            ).count(),
            
            # Departamentos
            'departments': Department.objects.annotate(
                employee_count=Count('employee')
            ),
            
            # Alertas
            'alerts': self.get_director_alerts(),
        }
    
    def get_jefe_recepcion_context(self):
        """Dashboard para Jefe de Recepción"""
        employee = self.request.user.employee
        team = employee.get_supervised_employees()
        today = timezone.now().date()

        # Filtrar checkins del día de hoy

        pending_checkins = Reservation.objects.filter(
                check_in_date=today,
                status='pending_checkin'
        )  
        
        completed_checkins = Reservation.objects.filter(
                check_in_date=today,
                status='checked_in'
                )
        
        total_chekins_count = pending_checkins.count() + completed_checkins.count()

        pending_checkouts = Reservation.objects.filter(
                check_out_date=today,
                status='pending_checkedout'
                )
        
        completed_checkouts = Reservation.objects.filter(
                check_in_date=today,
                status='checked_out'
                )
        
        total_checkouts_count = pending_checkouts.count() + completed_checkouts.count()

        return {
            # Mi equipo
            'team_size': team.count(),
            'team_present': Attendance.objects.filter(
                employee__in=team,
                check_in__date=today,
                check_out__isnull=True
            ).count(),
            'team_members': team.select_related('user', 'department'),
            'team_total': team.select_related('user', 'department').count(),
            # Habitaciones
            'available_rooms': Room.objects.filter(status='available').count(),
            'occupied_rooms': Room.objects.filter(status='occupied').count(),
            'clean_rooms': Room.objects.filter(status='clean').count(),
            'dirty_rooms': Room.objects.filter(status='dirty').count(),
            'total_rooms': Room.objects.filter(is_active=True).count(),
            'maintenance_rooms': Room.objects.filter(status='maintenance', is_active=True).count(),
            # Calcular tasa de ocupación
            'occupancy_rate': self._calculate_occupancy_rate(),
            # Permisos del equipo
            'pending_team_leaves': Leave.objects.filter(
                employee__in=team,
                status='pending'
            ).count(),
            'team_leaves': Leave.objects.filter(
                employee__in=team
            ).select_related('employee', 'employee__user').order_by('-created_at')[:10],
            # Check-ins/outs del día
            'pending_checkins': pending_checkins.count(),  
            'completed_checkins': completed_checkins.count(),
            'total_checkins': total_chekins_count,
            'pending_checkouts': pending_checkouts.count(),
            'completed_checkouts': completed_checkouts.count(),
            'total_checkouts': total_checkouts_count,
            'upcoming_checkins': [],
            # Cambios recientes en habitaciones
            'recent_room_changes': Room.objects.select_related(
            'room_type').order_by('-updated_at')[:10],
            # Alertas urgentes
            'urgent_issues': [], 
        }
       
    
    def get_recepcionista_context(self):
        """Dashboard para Recepcionista"""
        return {
            # Habitaciones
            
            # Mis datos
            'my_attendance_today': Attendance.objects.filter(
                employee=self.request.user.employee,
                check_in__date=timezone.now().date()
            ).first(),
            
            # Habitaciones por tipo
            'rooms_by_type': Room.objects.values(
                'room_type__name'
            ).annotate(
                total=Count('id'),
                available=Count('id', filter=Q(status='available'))
            ),
        }
    
    def get_jefe_limpieza_context(self):
        """Dashboard para Jefe de Limpieza"""
        employee = self.request.user.employee
        team = employee.get_supervised_employees()
        today = timezone.now().date()
        
        return {
            # Mi equipo
            'team_size': team.count(),
            'team_present': Attendance.objects.filter(
                employee__in=team,
                check_in__date=today,
                check_out__isnull=True
            ).count(),
            
            # Tareas de limpieza
            'pending_tasks': CleaningTask.objects.filter(
                status='pending'
            ).count(),
            'in_progress_tasks': CleaningTask.objects.filter(
                status='in_progress'
            ).count(),
            'completed_today': CleaningTask.objects.filter(
                status='completed',
                completed_at__date=today
            ).count(),
            
            # Habitaciones
            'dirty_rooms': Room.objects.filter(status='dirty').count(),
            'cleaning_rooms': Room.objects.filter(status='cleaning').count(),
            
            # Permisos del equipo
            'pending_team_leaves': Leave.objects.filter(
                employee__in=team,
                status='pending'
            ).count(),
            
            # Tareas sin asignar
            'unassigned_tasks': CleaningTask.objects.filter(
                assigned_to__isnull=True,
                status='pending'
            ).count(),
            
            # Productividad del equipo
            'team_productivity': self.get_cleaning_team_stats(team, today),
        }
    
    def get_camarero_piso_context(self):
        """Dashboard para Camarero de Piso"""
        employee = getattr(self.request.user, "employee", None)
        today = timezone.now().date()
        
        # Mis tareas
        if employee is None:
            my_tasks = CleaningTask.objects.none()
        else:
            my_tasks = CleaningTask.objects.filter(assigned_to=employee)
        
        return {
            # Mis tareas
            'pending_tasks': my_tasks.filter(status='pending').count(),
            'in_progress_tasks': my_tasks.filter(status='in_progress').count(),
            'completed_today': my_tasks.filter(
                status='completed'
            ).count(),
            
            # Próxima tarea
            'next_task': my_tasks.filter(
                status='pending'
            ).order_by('priority').first(),
            
            # Mi asistencia
            'my_attendance': Attendance.objects.filter(
                employee=employee,
                check_in__date=today
            ).first(),
            
            # Estadísticas del mes
            'month_completed': my_tasks.filter(
                status='completed'
            ).count(),
            
            # Mis tareas del día
            'today_tasks': my_tasks.filter(
                assigned_to=employee
            )
        }
    
    def get_jefe_mantenimiento_context(self):
        """Dashboard para Jefe de Mantenimiento"""
        employee = self.request.user.employee
        team = employee.get_supervised_employees()
        today = timezone.now().date()
        
        return {
            # Mi equipo
            'team_size': team.count(),
            'team_present': Attendance.objects.filter(
                employee__in=team,
                check_in__date=today,
                check_out__isnull=True
            ).count(),
            
            # Tareas de mantenimiento
            'pending_tasks': MaintenanceTask.objects.filter(
                status='pending'
            ).count(),
            'in_progress_tasks': MaintenanceTask.objects.filter(
                status='in_progress'
            ).count(),
            'urgent_tasks': MaintenanceTask.objects.filter(
                priority='high',
                status__in=['pending', 'in_progress']
            ).count(),
            
            # Habitaciones en mantenimiento
            'maintenance_rooms': Room.objects.filter(
                status='maintenance'
            ).count(),
            
            # Permisos del equipo
            'pending_team_leaves': Leave.objects.filter(
                employee__in=team,
                status='pending'
            ).count(),
        }
    
    def get_mantenimiento_context(self):
        """Dashboard para Personal de Mantenimiento"""
        employee = self.request.user.employee
        today = timezone.now().date()
        
        my_tasks = MaintenanceTask.objects.filter(assigned_to=employee)
        
        return {
            # Mis tareas
            'pending_tasks': my_tasks.filter(status='pending').count(),
            'in_progress_tasks': my_tasks.filter(status='in_progress').count(),
            'urgent_tasks': my_tasks.filter(
                priority='high',
                status__in=['pending', 'in_progress']
            ).count(),
            
            # Próxima tarea
            'next_task': my_tasks.filter(
                status='pending'
            ).order_by('-priority').first(),
            
            # Mi asistencia
            'my_attendance': Attendance.objects.filter(
                employee=employee,
                check_in__date=today
            ).first(),
            
            # Mis tareas del día
            'today_tasks': my_tasks.filter(
                assigned_to=employee
            ),
        }
    
    def get_rrhh_context(self):
        """Dashboard para RRHH"""
        today = timezone.now().date()
        first_day_month = today.replace(day=1)
        
        return {
            # Empleados
            'total_employees': Employee.objects.count(),
            'active_employees': Employee.objects.filter(is_available=True).count(),
            
            # Asistencia hoy
            'present_today': Attendance.objects.filter(
                check_in__date=today,
                check_out__isnull=True
            ).count(),
            'absent_today': Employee.objects.count() - Attendance.objects.filter(
                check_in__date=today
            ).count(),
            'late_today': Attendance.objects.filter(
                check_in__date=today,
                status='late'
            ).count(),
            
            # Permisos
            'pending_leaves': Leave.objects.filter(status='pending').count(),
            'approved_leaves_month': Leave.objects.filter(
                status='approved',
                start_date__gte=first_day_month
            ).count(),
            
            # Departamentos
            'departments': Department.objects.annotate(
                employee_count=Count('employee')
            ),
            
            # Nuevos empleados este mes
            'new_employees_month': Employee.objects.filter(
                hire_date__gte=first_day_month
            ).count(),
        }
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def get_director_alerts(self):
        """Genera alertas para el director"""
        alerts = []
        
        # Permisos pendientes
        pending_leaves = Leave.objects.filter(status='pending').count()
        if pending_leaves > 5:
            alerts.append({
                'type': 'warning',
                'message': f'{pending_leaves} solicitudes de permiso pendientes',
                'icon': 'calendar-times'
            })
        
        # Tareas urgentes
        urgent_maintenance = MaintenanceTask.objects.filter(
            priority='high',
            status='pending'
        ).count()
        if urgent_maintenance > 0:
            alerts.append({
                'type': 'danger',
                'message': f'{urgent_maintenance} tareas urgentes de mantenimiento',
                'icon': 'exclamation-triangle'
            })
        
        # Habitaciones fuera de servicio
        maintenance_rooms = Room.objects.filter(status='maintenance').count()
        if maintenance_rooms > 3:
            alerts.append({
                'type': 'info',
                'message': f'{maintenance_rooms} habitaciones en mantenimiento',
                'icon': 'tools'
            })
        
        return alerts
    
    def get_reception_alerts(self, dirty_rooms, maintenance_rooms):
        """Genera alertas específicas para recepción"""
        alerts = []
    
        if dirty_rooms > 5:
            alerts.append({
                'title': 'Habitaciones Sucias',
                'description': f'Hay {dirty_rooms} habitaciones pendientes de limpieza'
            })
    
        if maintenance_rooms > 2:
            alerts.append({
                'title': 'Habitaciones en Mantenimiento',
                'description': f'{maintenance_rooms} habitaciones no disponibles por mantenimiento'
            })
    
        return alerts
    
    def get_cleaning_team_stats(self, team, today):
        """Estadísticas de productividad del equipo de limpieza"""
        stats = []
        
        for employee in team:
            completed = CleaningTask.objects.filter(
                assigned_to=employee,
                status='completed'
            ).count()
            
            stats.append({
                'employee': employee,
                'completed_today': completed
            })
        
        return sorted(stats, key=lambda x: x['completed_today'], reverse=True)[:5]

    


"""
# apps/dashboard/views.py
from django.shortcuts import render
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from apps.rooms.models import Room, CleaningTask, MaintenanceRequest
from apps.employees.models import Department


# apps/dashboard/views.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class HomeView(LoginRequiredMixin, TemplateView):
    #Dashboard principal que redirige según rol
    
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

def home(request):
   # Dashboard principal con estadísticas
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


    """