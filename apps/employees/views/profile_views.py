# apps/employees/views/profile_views.py
from django.shortcuts import render, redirect
from django.views.generic import DetailView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg

from apps.employees.models import Employee
from apps.employees.forms import EmployeeForm
from apps.attendance.models import Attendance
from apps.leave.models import Leave
from apps.rooms.models import CleaningTask, MaintenanceTask


class MyProfileView(LoginRequiredMixin, DetailView):
    """Vista del perfil del usuario actual"""
    model = Employee
    template_name = 'employees/profiles/MyProfile.html'
    context_object_name = 'employee'
    
    def get_object(self):
        """Obtiene el perfil del usuario actual"""
        return self.request.user.employee
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.object
        today = timezone.now().date()
        
        # Información básica
        context['today'] = today
        
        # Asistencia actual
        context['current_attendance'] = employee.get_current_attendance()
        context['is_checked_in'] = employee.is_checked_in()
        
        # Estadísticas del mes actual
        first_day_month = today.replace(day=1)
        monthly_attendances = employee.attendances.filter(
            check_in__gte=first_day_month,
            check_out__isnull=False
        )
        
        # Calcular horas trabajadas
        total_hours = timedelta()
        for attendance in monthly_attendances:
            total_hours += attendance.duration()
        
        days_worked = monthly_attendances.count()
        avg_hours = total_hours / days_worked if days_worked > 0 else timedelta()
        
        context['monthly_stats'] = {
            'days_worked': days_worked,
            'total_hours': self._format_timedelta(total_hours),
            'average_hours': self._format_timedelta(avg_hours),
            'late_arrivals': monthly_attendances.filter(status='late').count(),
        }
        
        # Permisos
        context['pending_leaves'] = employee.leaves.filter(status='pending').count()
        context['approved_leaves'] = employee.leaves.filter(
            status='approved',
            start_date__gte=today
        ).order_by('start_date')[:3]
        
        # Asistencias recientes
        context['recent_attendances'] = employee.attendances.all()[:5]
        
        # Estadísticas específicas por rol
        context['role_stats'] = self._get_role_specific_stats(employee)
        
        return context
    
    def _format_timedelta(self, td):
        """Formatea un timedelta a horas y minutos"""
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return {'hours': hours, 'minutes': minutes}
    
    def _get_role_specific_stats(self, employee):
        """Obtiene estadísticas específicas según el rol"""
        today = timezone.now().date()
        first_day_month = today.replace(day=1)
        
        stats = {}
        
        # Estadísticas para limpieza
        if employee.role in ['jefe_limpieza', 'camarero_piso']:
            tasks = CleaningTask.objects.filter(assigned_to=employee)
            stats['cleaning'] = {
                'total_month': tasks.filter(created_at__gte=first_day_month).count(),
                'completed_month': tasks.filter(
                    status='completed',
                    completed_at__gte=first_day_month
                ).count(),
                'pending': tasks.filter(status='pending').count(),
                'in_progress': tasks.filter(status='in_progress').count(),
            }
        
        # Estadísticas para mantenimiento
        elif employee.role in ['jefe_mantenimiento', 'mantenimiento']:
            tasks = MaintenanceTask.objects.filter(assigned_to=employee)
            stats['maintenance'] = {
                'total_month': tasks.filter(created_at__gte=first_day_month).count(),
                'completed_month': tasks.filter(
                    status='completed',
                    resolved_at__gte=first_day_month
                ).count(),
                'pending': tasks.filter(status='pending').count(),
                'urgent': tasks.filter(status__in=['pending', 'in_progress'], priority='urgent').count(),
            }
        
        # Estadísticas para supervisores
        if employee.is_supervisor():
            team = employee.get_supervised_employees()
            stats['team'] = {
                'size': team.count(),
                'present_today': Attendance.objects.filter(
                    employee__in=team,
                    check_in__date=today,
                    check_out__isnull=True
                ).count(),
                'pending_leaves': Leave.objects.filter(
                    employee__in=team,
                    status='pending'
                ).count(),
            }
        
        return stats


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar el perfil del usuario"""
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/profiles/ProfileUpdate.html'
    success_url = reverse_lazy('profiles:my-profile')
    
    def get_object(self):
        """Obtiene el perfil del usuario actual"""
        return self.request.user.employee
    
    def form_valid(self, form):
        messages.success(
            self.request,
            'Tu perfil ha sido actualizado exitosamente.'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Mi Perfil'
        context['button_text'] = 'Guardar Cambios'
        return context


class ProfileStatsView(LoginRequiredMixin, TemplateView):
    """Vista detallada de estadísticas del perfil"""
    template_name = 'employees/profiles/ProfileStats.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.request.user.employee
        today = timezone.now().date()
        
        # Período seleccionado (por defecto mes actual)
        period = self.request.GET.get('period', 'month')
        
        if period == 'week':
            start_date = today - timedelta(days=7)
            period_name = 'Última Semana'
        elif period == 'year':
            start_date = today.replace(month=1, day=1)
            period_name = 'Este Año'
        else:  # month
            start_date = today.replace(day=1)
            period_name = 'Este Mes'
        
        context['period'] = period
        context['period_name'] = period_name
        context['start_date'] = start_date
        
        # Asistencias del período
        attendances = employee.attendances.filter(
            check_in__date__gte=start_date,
            check_in__date__lte=today
        )
        
        # Estadísticas de asistencia
        total_hours = timedelta()
        on_time = 0
        late = 0
        
        for attendance in attendances:
            if attendance.check_out:
                total_hours += attendance.duration()
            if attendance.status == 'present':
                on_time += 1
            elif attendance.status == 'late':
                late += 1
        
        total_days = attendances.count()
        avg_hours = total_hours / total_days if total_days > 0 else timedelta()
        
        context['attendance_stats'] = {
            'total_days': total_days,
            'on_time': on_time,
            'late': late,
            'total_hours': self._format_timedelta(total_hours),
            'average_hours': self._format_timedelta(avg_hours),
            'punctuality_rate': round((on_time / total_days * 100), 1) if total_days > 0 else 0,
        }
        
        # Datos para gráficos
        context['daily_hours'] = self._get_daily_hours_data(attendances, start_date, today)
        context['attendance_by_status'] = self._get_attendance_by_status(attendances)
        
        # Permisos del período
        leaves = employee.leaves.filter(
            start_date__gte=start_date,
            start_date__lte=today
        )
        
        context['leave_stats'] = {
            'total': leaves.count(),
            'approved': leaves.filter(status='approved').count(),
            'pending': leaves.filter(status='pending').count(),
            'rejected': leaves.filter(status='rejected').count(),
        }
        
        # Tareas específicas por rol
        if employee.role in ['camarero_piso', 'jefe_limpieza']:
            context['task_stats'] = self._get_cleaning_task_stats(employee, start_date, today)
        elif employee.role in ['mantenimiento', 'jefe_mantenimiento']:
            context['task_stats'] = self._get_maintenance_task_stats(employee, start_date, today)
        
        return context
    
    def _format_timedelta(self, td):
        """Formatea un timedelta"""
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return {'hours': hours, 'minutes': minutes}
    
    def _get_daily_hours_data(self, attendances, start_date, end_date):
        """Obtiene datos de horas trabajadas por día"""
        daily_data = {}
        current_date = start_date
        
        while current_date <= end_date:
            day_attendances = attendances.filter(check_in__date=current_date)
            total_hours = sum(
                (att.duration().total_seconds() / 3600) 
                for att in day_attendances 
                if att.check_out
            )
            daily_data[current_date.strftime('%d/%m')] = round(total_hours, 2)
            current_date += timedelta(days=1)
        
        return daily_data
    
    def _get_attendance_by_status(self, attendances):
        """Obtiene distribución de asistencias por estado"""
        return {
            'present': attendances.filter(status='present').count(),
            'late': attendances.filter(status='late').count(),
        }
    
    def _get_cleaning_task_stats(self, employee, start_date, end_date):
        """Estadísticas de tareas de limpieza"""
        tasks = CleaningTask.objects.filter(
            assigned_to=employee,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        return {
            'total': tasks.count(),
            'completed': tasks.filter(status='completed').count(),
            'pending': tasks.filter(status='pending').count(),
            'in_progress': tasks.filter(status='in_progress').count(),
        }
    
    def _get_maintenance_task_stats(self, employee, start_date, end_date):
        """Estadísticas de tareas de mantenimiento"""
        tasks = MaintenanceTask.objects.filter(
            assigned_to=employee,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        return {
            'total': tasks.count(),
            'completed': tasks.filter(status='completed').count(),
            'pending': tasks.filter(status='pending').count(),
            'urgent': tasks.filter(priority='urgent').count(),
        }