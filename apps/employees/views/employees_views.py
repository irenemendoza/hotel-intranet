from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta

from apps.employees.models import Employee, Department 
from apps.attendance.models import Attendance
from apps.leave.models import Leave
from apps.employees.forms import EmployeeForm



# ==================== EMPLOYEE VIEWS ====================

class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'employees/EmployeesList.html'
    context_object_name = 'employees'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('user', 'department')
        
        # Filtros
        department = self.request.GET.get('department')
        search = self.request.GET.get('search')
        available = self.request.GET.get('available')
        
        if department:
            queryset = queryset.filter(department_id=department)
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(employee_number__icontains=search) |
                Q(position__icontains=search)
            )
        if available:
            queryset = queryset.filter(is_available=True)
        
        return queryset.order_by('user__first_name', 'user__last_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.filter(is_active=True)
        context['total_employees'] = Employee.objects.count()
        context['available_employees'] = Employee.objects.filter(is_available=True).count()
        
        # Empleados fichados actualmente
        context['checked_in_count'] = Attendance.objects.filter(
            check_out__isnull=True
        ).count()
        
        return context


class EmployeeDetailView(LoginRequiredMixin, DetailView):
    model = Employee
    template_name = 'employees/EmployeeDetail.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Asistencias recientes
        context['recent_attendances'] = self.object.attendances.all()[:10]

        # Asistencia actual
        context['current_attendance'] = self.object.get_current_attendance()

        # Permisos
        context['pending_leaves'] = self.object.leaves.filter(status='pending')
        context['approved_leaves'] = self.object.leaves.filter(status='approved').order_by('-start_date')[:5]

        # Estadísticas del mes actual
        today = timezone.now()
        first_day_month = today.replace(day=1)

        monthly_attendances = self.object.attendances.filter(
            check_in__gte=first_day_month,
            check_out__isnull=False
        )

        total_hours = timedelta()
        for attendance in monthly_attendances:
            total_hours += attendance.duration()

        count_days = monthly_attendances.count()
        average_hours = total_hours / count_days if count_days > 0 else timedelta()

        # Convertir a horas y minutos
        total_seconds = int(total_hours.total_seconds())
        average_seconds = int(average_hours.total_seconds())

        context['monthly_stats'] = {
            'days_worked': count_days,
            'total_hours_h': total_seconds // 3600,
            'total_hours_m': (total_seconds % 3600) // 60,
            'average_hours_h': average_seconds // 3600,
            'average_hours_m': (average_seconds % 3600) // 60,
        }

        return context



class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/EmployeeForm.html'
    success_url = reverse_lazy('employees:list')
    
    def form_valid(self, form):
        # Crear el usuario primero
        from django.contrib.auth.models import User
        
        username = form.cleaned_data['email'].split('@')[0]
        user = User.objects.create_user(
            username=username,
            email=form.cleaned_data['email'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name']
        )
        
        # Asignar el usuario al perfil
        form.instance.user = user
        
        messages.success(
            self.request, 
            f'Empleado {form.instance.get_full_name()} creado exitosamente.'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Empleado'
        context['button_text'] = 'Crear'
        return context


class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/EmployeeForm.html'
    
    def get_success_url(self):
        return reverse_lazy('employees:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Empleado {form.instance.get_full_name()} actualizado exitosamente.'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Empleado'
        context['button_text'] = 'Actualizar'
        return context


class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employee
    template_name = 'employees/EmployeeDelete.html'
    context_object_name = 'employee'
    success_url = reverse_lazy('employees:list')
    
    def delete(self, request, *args, **kwargs):
        employee = self.get_object()
        user = employee.user
        
        messages.success(request, f'Empleado {employee.get_full_name()} eliminado exitosamente.')
        
        # Eliminar el usuario también
        result = super().delete(request, *args, **kwargs)
        user.delete()
        
        return result


