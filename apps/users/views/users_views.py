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

from ..models import UserProfile, Department, Attendance, Leave
from ..forms import (
    UserProfileForm, AttendanceCheckInForm, AttendanceCheckOutForm,
    LeaveRequestForm, LeaveApprovalForm
)


# ==================== EMPLOYEE VIEWS ====================

class EmployeeListView(LoginRequiredMixin, ListView):
    model = UserProfile
    template_name = 'users/employees/EmployeesList.html'
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
        context['total_employees'] = UserProfile.objects.count()
        context['available_employees'] = UserProfile.objects.filter(is_available=True).count()
        
        # Empleados fichados actualmente
        context['checked_in_count'] = Attendance.objects.filter(
            check_out__isnull=True
        ).count()
        
        return context


class EmployeeDetailView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = 'users/employees/EmployeeDetail.html'
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
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'users/employees/EmployeeForm.html'
    success_url = reverse_lazy('users:employee-list')
    
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
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'users/employees/EmployeeForm.html'
    
    def get_success_url(self):
        return reverse_lazy('users:employee-detail', kwargs={'pk': self.object.pk})
    
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
    model = UserProfile
    template_name = 'users/employees/EmployeeDelete.html'
    context_object_name = 'employee'
    success_url = reverse_lazy('users:employee-list')
    
    def delete(self, request, *args, **kwargs):
        employee = self.get_object()
        user = employee.user
        
        messages.success(request, f'Empleado {employee.get_full_name()} eliminado exitosamente.')
        
        # Eliminar el usuario también
        result = super().delete(request, *args, **kwargs)
        user.delete()
        
        return result


# ==================== ATTENDANCE / FICHAJE ====================

class AttendanceDashboardView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = 'users/attendance/AttendanceDashboard.html'
    context_object_name = 'attendances'
    
    def get_queryset(self):
        today = timezone.now().date()
        return Attendance.objects.filter(
            check_in__date=today
        ).select_related('employee', 'employee__user', 'employee__department').order_by('-check_in')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = timezone.now().date()
        
        # Estadísticas del día
        context['stats'] = {
            'checked_in': Attendance.objects.filter(
                check_in__date=today,
                check_out__isnull=True
            ).count(),
            'checked_out': Attendance.objects.filter(
                check_in__date=today,
                check_out__isnull=False
            ).count(),
            'total_employees': UserProfile.objects.count(),
            'on_leave': Leave.objects.filter(
                status='approved',
                start_date__lte=today,
                end_date__gte=today
            ).count()
        }
        
        # Empleados que no han fichado
        checked_in_employees = Attendance.objects.filter(
            check_in__date=today
        ).values_list('employee_id', flat=True)
        
        context['not_checked_in'] = UserProfile.objects.exclude(
            id__in=checked_in_employees
        ).select_related('user', 'department')[:10]
        
        return context


class MyAttendanceView(LoginRequiredMixin, View):
    """Vista principal de fichaje para el empleado"""
    template_name = 'users/attendance/MyAttendance.html'
    
    def get(self, request):
        profile = request.user.profile
        current_attendance = profile.get_current_attendance()
        today_hours = profile.get_today_work_hours()

        if today_hours:
            total_seconds = int(today_hours.total_seconds())
            today_hours_h = total_seconds // 3600
            today_hours_m = (total_seconds % 3600) // 60
        else:
            today_hours_h = 0
            today_hours_m = 0

        
        # Historial reciente
        recent_attendances = profile.attendances.all()[:10]
        
        context = {
            'profile': profile,
            'current_attendance': current_attendance,
            'is_checked_in': profile.is_checked_in(),
            'recent_attendances': recent_attendances,
            'check_in_form': AttendanceCheckInForm(),
            'check_out_form': AttendanceCheckOutForm(),
            'today_hours_h': today_hours_h,
            'today_hours_m': today_hours_m,
        }

        return render(request, self.template_name, context)


class AttendanceCheckInView(LoginRequiredMixin, View):
    """Vista para fichar entrada"""
    
    def post(self, request):
        profile = request.user.profile
        
        # Verificar que no esté ya fichado
        if profile.is_checked_in():
            messages.warning(request, 'Ya has fichado tu entrada. Debes fichar la salida primero.')
            return redirect('attendance:my-attendance')
        
        form = AttendanceCheckInForm(request.POST)
        
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.employee = profile
            attendance.check_in = timezone.now()
            
            # Determinar si llega tarde (después de las 9:00 AM)
            if attendance.check_in.time().hour >= 9:
                attendance.status = Attendance.StatusChoices.LATE
            else:
                attendance.status = Attendance.StatusChoices.PRESENT
            
            attendance.save()
            
            messages.success(
                request, 
                f'¡Entrada registrada! Hora: {attendance.check_in.strftime("%H:%M")}'
            )
        else:
            messages.error(request, 'Error al registrar la entrada.')
        
        return redirect('attendance:my-attendance')


class AttendanceCheckOutView(LoginRequiredMixin, View):
    """Vista para fichar salida"""
    
    def post(self, request):
        profile = request.user.profile
        attendance = profile.get_current_attendance()
        
        if not attendance:
            messages.warning(request, 'No tienes una entrada registrada hoy.')
            return redirect('attendance:my-attendance')
        
        form = AttendanceCheckOutForm(request.POST, instance=attendance)
        
        if form.is_valid():
            attendance = form.save()
            
            messages.success(
                request,
                f'¡Salida registrada! Duración: {attendance.duration_formatted()}'
            )
        else:
            messages.error(request, 'Error al registrar la salida.')
        
        return redirect('attendance:my-attendance')


class AttendanceHistoryView(LoginRequiredMixin, ListView):
    """Historial completo de asistencias del empleado"""
    model = Attendance
    template_name = 'users/attendance/AttendanceHistory.html'
    context_object_name = 'attendances'
    paginate_by = 20
    
    def get_queryset(self):
        return Attendance.objects.filter(
            employee=self.request.user.profile
        ).order_by('-check_in')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas del mes
        today = timezone.now()
        first_day_month = today.replace(day=1)
        
        monthly_attendances = self.get_queryset().filter(
            check_in__gte=first_day_month,
            check_out__isnull=False
        )
        
        total_hours = timedelta()
        for attendance in monthly_attendances:
            total_hours += attendance.duration()
        
        context['monthly_stats'] = {
            'days_worked': monthly_attendances.count(),
            'total_hours': total_hours,
            'late_count': monthly_attendances.filter(status='late').count()
        }
        
        return context


# ==================== LEAVE / PERMISOS ====================

class LeaveListView(LoginRequiredMixin, ListView):
    """Lista de permisos (para el empleado)"""
    model = Leave
    template_name = 'users/leaves/LeaveList.html'
    context_object_name = 'leaves'
    paginate_by = 20
    
    def get_queryset(self):
        return Leave.objects.filter(
            employee=self.request.user.profile
        ).order_by('-created_at')


class LeaveCreateView(LoginRequiredMixin, CreateView):
    """Solicitar un permiso"""
    model = Leave
    form_class = LeaveRequestForm
    template_name = 'users/leaves/LeaveForm.html'
    success_url = reverse_lazy('attendance:leave-list')
    
    def form_valid(self, form):
        form.instance.employee = self.request.user.profile
        messages.success(self.request, 'Solicitud de permiso enviada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Solicitar Permiso'
        context['button_text'] = 'Enviar Solicitud'
        return context


class LeaveDetailView(LoginRequiredMixin, DetailView):
    """Detalle de un permiso"""
    model = Leave
    template_name = 'users/leaves/LeaveDetail.html'
    context_object_name = 'leave'


class LeaveManagementView(LoginRequiredMixin, ListView):
    """Gestión de permisos (para supervisores/RRHH)"""
    model = Leave
    template_name = 'users/leaves/LeaveManagement.html'
    context_object_name = 'leaves'
    paginate_by = 20
    
    def get_queryset(self):
        status = self.request.GET.get('status', 'pending')
        queryset = Leave.objects.select_related('employee', 'employee__user').order_by('-created_at')
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas
        context['stats'] = {
            'pending': Leave.objects.filter(status='pending').count(),
            'approved': Leave.objects.filter(status='approved').count(),
            'rejected': Leave.objects.filter(status='rejected').count()
        }
        
        return context


class LeaveApprovalView(LoginRequiredMixin, UpdateView):
    """Aprobar/Rechazar permiso"""
    model = Leave
    form_class = LeaveApprovalForm
    template_name = 'users/leaves/LeaveApproval.html'
    success_url = reverse_lazy('attendance:leave-management')
    
    def form_valid(self, form):
        form.save(user=self.request.user)
        
        leave = self.object
        if leave.status == 'approved':
            messages.success(self.request, f'Permiso aprobado para {leave.employee.get_full_name()}')
        else:
            messages.warning(self.request, f'Permiso rechazado para {leave.employee.get_full_name()}')
        
        return super().form_valid(form)


# ==================== ATTENDANCE REPORTS ====================

class AttendanceReportView(LoginRequiredMixin, ListView):
    """Reporte de asistencias por fecha"""
    model = Attendance
    template_name = 'users/attendance/AttendanceReport.html'
    context_object_name = 'attendances'
    
    def get_queryset(self):
        # Obtener fecha de los parámetros GET o usar hoy
        date_str = self.request.GET.get('date')
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                date = timezone.now().date()
        else:
            date = timezone.now().date()
        
        self.date = date
        
        return Attendance.objects.filter(
            check_in__date=date
        ).select_related('employee', 'employee__user', 'employee__department').order_by('employee__user__first_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['date'] = self.date
        context['total_attendances'] = self.get_queryset().count()
        context['checked_out_count'] = self.get_queryset().filter(check_out__isnull=False).count()
        
        return context