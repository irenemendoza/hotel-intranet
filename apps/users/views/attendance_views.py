from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from ..models import Attendance, UserProfile, Leave


class AttendanceDashboardView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = 'users/attendance/AttendanceDashboard.html'
    context_object_name = 'today_attendances'
    
    def get_queryset(self):
        today = timezone.now().date()
        return Attendance.objects.filter(
            check_in__date=today
        ).select_related('employee', 'employee__user').order_by('-check_in')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = timezone.now().date()
        
        # Total de empleados activos
        total_employees = UserProfile.objects.filter(is_active=True).count()
        
        # Estadísticas del día actual
        today_stats = {
            'present': Attendance.objects.filter(
                check_in__date=today,
                status__in=['present', 'late']
            ).count(),
            'absent': total_employees - Attendance.objects.filter(
                check_in__date=today
            ).count(),
            'late': Attendance.objects.filter(
                check_in__date=today,
                status='late'
            ).count(),
            'on_leave': Leave.objects.filter(
                status='approved',
                start_date__lte=today,
                end_date__gte=today
            ).count()
        }
        
        # Calcular porcentaje de presentes
        if total_employees > 0:
            today_stats['present_percentage'] = round(
                (today_stats['present'] / total_employees) * 100, 1
            )
        else:
            today_stats['present_percentage'] = 0
        
        context['today_stats'] = today_stats
        context['today'] = today
        
        # Asistencia del usuario actual
        if hasattr(self.request.user, 'profile'):
            context['today_attendance'] = Attendance.objects.filter(
                employee=self.request.user.profile,
                check_in__date=today
            ).first()
        
        # Datos para gráfico semanal (últimos 7 días)
        week_ago = today - timedelta(days=6)
        weekly_data = []
        weekly_labels = []
        
        for i in range(7):
            day = week_ago + timedelta(days=i)
            count = Attendance.objects.filter(
                check_in__date=day,
                status__in=['present', 'late']
            ).count()
            weekly_data.append(count)
            weekly_labels.append(day.strftime('%d/%m'))
        
        context['weekly_data'] = weekly_data
        context['weekly_labels'] = weekly_labels
        
        # Estadísticas mensuales
        first_day_month = today.replace(day=1)
        
        month_attendances = Attendance.objects.filter(
            check_in__date__gte=first_day_month,
            check_in__date__lte=today
        )
        
        month_stats = {
            'worked_days': month_attendances.values('check_in__date').distinct().count(),
            'absences': 0,  # Ajustar según tu lógica
            'late_arrivals': month_attendances.filter(status='late').count()
        }
        
        # Calcular porcentajes
        days_in_month = (today - first_day_month).days + 1
        if days_in_month > 0:
            month_stats['worked_percentage'] = round(
                (month_stats['worked_days'] / days_in_month) * 100, 1
            )
            month_stats['absence_percentage'] = round(
                (month_stats['absences'] / days_in_month) * 100, 1
            )
            month_stats['late_percentage'] = round(
                (month_stats['late_arrivals'] / days_in_month) * 100, 1
            )
        else:
            month_stats['worked_percentage'] = 0
            month_stats['absence_percentage'] = 0
            month_stats['late_percentage'] = 0
        
        context['month_stats'] = month_stats
        
        return context


class MyAttendanceView(LoginRequiredMixin, View):
    """Vista principal de fichaje para el empleado"""
    template_name = 'users/attendance/MyAttendance.html'
    
    def get(self, request):
        profile = request.user.profile
        
        # Obtener asistencia actual del día
        today = timezone.now().date()
        current_attendance = Attendance.objects.filter(
            employee=profile,
            check_in__date=today
        ).first()
        
        # Calcular horas trabajadas hoy
        if current_attendance and current_attendance.check_out:
            duration = current_attendance.check_out - current_attendance.check_in
            total_seconds = int(duration.total_seconds())
            today_hours_h = total_seconds // 3600
            today_hours_m = (total_seconds % 3600) // 60
        elif current_attendance and not current_attendance.check_out:
            # Si está fichado pero no ha salido, calcular tiempo hasta ahora
            duration = timezone.now() - current_attendance.check_in
            total_seconds = int(duration.total_seconds())
            today_hours_h = total_seconds // 3600
            today_hours_m = (total_seconds % 3600) // 60
        else:
            today_hours_h = 0
            today_hours_m = 0
        
        # Historial reciente
        recent_attendances = Attendance.objects.filter(
            employee=profile
        ).order_by('-check_in')[:10]
        
        context = {
            'profile': profile,
            'current_attendance': current_attendance,
            'is_checked_in': current_attendance is not None and current_attendance.check_out is None,
            'recent_attendances': recent_attendances,
            'today_hours_h': today_hours_h,
            'today_hours_m': today_hours_m,
        }

        return render(request, self.template_name, context)


class AttendanceCheckInView(LoginRequiredMixin, View):
    """Vista para fichar entrada"""
    
    def post(self, request):
        profile = request.user.profile
        today = timezone.now().date()
        
        # Verificar que no esté ya fichado
        existing = Attendance.objects.filter(
            employee=profile,
            check_in__date=today
        ).first()
        
        if existing:
            messages.warning(request, 'Ya has fichado tu entrada hoy.')
            return redirect('attendance:my-attendance')
        
        # Crear nuevo registro de asistencia
        attendance = Attendance.objects.create(
            employee=profile,
            check_in=timezone.now()
        )
        
        # Determinar si llega tarde (después de las 9:00 AM)
        if attendance.check_in.time().hour >= 9:
            attendance.status = 'late'
        else:
            attendance.status = 'present'
        
        attendance.save()
        
        messages.success(
            request, 
            f'¡Entrada registrada! Hora: {attendance.check_in.strftime("%H:%M")}'
        )
        
        return redirect('attendance:my-attendance')


class AttendanceCheckOutView(LoginRequiredMixin, View):
    """Vista para fichar salida"""
    
    def post(self, request):
        profile = request.user.profile
        today = timezone.now().date()
        
        # Buscar asistencia del día sin salida registrada
        attendance = Attendance.objects.filter(
            employee=profile,
            check_in__date=today,
            check_out__isnull=True
        ).first()
        
        if not attendance:
            messages.warning(request, 'No tienes una entrada registrada hoy o ya has fichado la salida.')
            return redirect('attendance:my-attendance')
        
        # Registrar salida
        attendance.check_out = timezone.now()
        attendance.save()
        
        # Calcular duración
        duration = attendance.check_out - attendance.check_in
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        
        messages.success(
            request,
            f'¡Salida registrada! Duración: {hours}h {minutes}m'
        )
        
        return redirect('attendance:my-attendance')


class AttendanceHistoryView(LoginRequiredMixin, ListView):
    """Historial completo de asistencias del empleado"""
    model = Attendance
    template_name = 'users/attendance/AttendanceHistory.html'
    context_object_name = 'attendances'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Attendance.objects.filter(
            employee=self.request.user.profile
        ).order_by('-check_in')
        
        # Aplicar filtros si existen
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        status = self.request.GET.get('status')
        
        if start_date:
            queryset = queryset.filter(check_in__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(check_in__date__lte=end_date)
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = timezone.now().date()
        first_day_month = today.replace(day=1)
        
        # Filtrar solo las del usuario actual
        monthly_attendances = Attendance.objects.filter(
            employee=self.request.user.profile,
            check_in__date__gte=first_day_month,
            check_out__isnull=False
        )
        
        # Calcular horas totales
        total_hours = timedelta()
        for attendance in monthly_attendances:
            if attendance.check_out:
                duration = attendance.check_out - attendance.check_in
                total_hours += duration
        
        # Convertir a horas
        total_hours_decimal = total_hours.total_seconds() / 3600
        
        context['summary'] = {
            'total_days': monthly_attendances.count(),
            'late_count': monthly_attendances.filter(status='late').count(),
            'absent_count': 0,  # Ajustar según tu lógica
            'total_hours': round(total_hours_decimal, 1)
        }
        
        context['today'] = today
        
        return context


class AttendanceReportView(LoginRequiredMixin, View):
    """Vista para generar reportes de asistencia"""
    template_name = 'users/attendance/AttendanceReport.html'
    
    def get(self, request):
        context = {
            'years': range(timezone.now().year - 2, timezone.now().year + 1),
            'current_year': timezone.now().year,
            'recent_reports': []  # Aquí puedes agregar lógica para reportes guardados
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        # Aquí implementarías la lógica para generar el reporte
        report_type = request.POST.get('report_type')
        format_type = request.POST.get('format')
        
        # Por ahora solo redirige de vuelta
        messages.success(request, 'Funcionalidad de reportes en desarrollo')
        return redirect('attendance:report')