from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from apps.leave.models import Leave

from .models import Attendance


class AttendanceDashboardView(LoginRequiredMixin, ListView):
    """Dashboard with attendance statistics"""

    model = Attendance
    template_name = "attendance/AttendanceDashboard.html"
    context_object_name = "today_attendances"

    def get_queryset(self):
        today = timezone.now().date()
        return (
            Attendance.objects.filter(check_in__date=today)
            .select_related("employee", "employee__user")
            .order_by("-check_in")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.now().date()

        # Total active employees
        total_employees = Attendance.objects.filter(check_out__isnull=True).count()

        # Today's statistics
        today_stats = {
            "present": Attendance.objects.filter(
                check_in__date=today, status__in=["present", "late"]
            ).count(),
            "absent": total_employees
            - Attendance.objects.filter(check_in__date=today).count(),
            "late": Attendance.objects.filter(
                check_in__date=today, status="late"
            ).count(),
            "on_leave": Leave.objects.filter(
                status="approved", start_date__lte=today, end_date__gte=today
            ).count(),
        }

        # Calculate present percentage
        if total_employees > 0:
            today_stats["present_percentage"] = round(
                (today_stats["present"] / total_employees) * 100, 1
            )
        else:
            today_stats["present_percentage"] = 0

        context["today_stats"] = today_stats
        context["today"] = today

        # Current user's attendacence
        if hasattr(self.request.user, "employee"):
            context["today_attendance"] = Attendance.objects.filter(
                employee=self.request.user.employee, check_in__date=today
            ).first()

        # Weekly chart data (last 7 days)
        week_ago = today - timedelta(days=6)
        weekly_data = []
        weekly_labels = []

        for i in range(7):
            day = week_ago + timedelta(days=i)
            count = Attendance.objects.filter(
                check_in__date=day, status__in=["present", "late"]
            ).count()
            weekly_data.append(count)
            weekly_labels.append(day.strftime("%d/%m"))

        context["weekly_data"] = weekly_data
        context["weekly_labels"] = weekly_labels

        # Monthly statistics
        first_day_month = today.replace(day=1)

        month_attendances = Attendance.objects.filter(
            check_in__date__gte=first_day_month, check_in__date__lte=today
        )

        month_stats = {
            "worked_days": month_attendances.values("check_in__date")
            .distinct()
            .count(),
            "absences": 0,  # Ajustar según tu lógica
            "late_arrivals": month_attendances.filter(status="late").count(),
        }

        # Calculate percentages
        days_in_month = (today - first_day_month).days + 1
        if days_in_month > 0:
            month_stats["worked_percentage"] = round(
                (month_stats["worked_days"] / days_in_month) * 100, 1
            )
            month_stats["absence_percentage"] = round(
                (month_stats["absences"] / days_in_month) * 100, 1
            )
            month_stats["late_percentage"] = round(
                (month_stats["late_arrivals"] / days_in_month) * 100, 1
            )
        else:
            month_stats["worked_percentage"] = 0
            month_stats["absence_percentage"] = 0
            month_stats["late_percentage"] = 0

        context["month_stats"] = month_stats

        return context


class MyAttendanceView(LoginRequiredMixin, View):
    """Main attendance view for employees"""

    template_name = "attendance/MyAttendance.html"

    def get(self, request):
        employee = request.user.employee

        # Get today's attendance
        today = timezone.now().date()
        current_attendance = Attendance.objects.filter(
            employee=employee, check_in__date=today
        ).first()

        # Calculate hours worked today
        if current_attendance:
            duration = current_attendance.duration
            total_seconds = int(duration.total_seconds())
            today_hours_h = total_seconds // 3600
            today_hours_m = (total_seconds % 3600) // 60
        else:
            today_hours_h = 0
            today_hours_m = 0

        # Recent attendance history
        recent_attendances = Attendance.objects.filter(employee=employee).order_by(
            "-check_in"
        )[:10]

        context = {
            "employee": employee,
            "current_attendance": current_attendance,
            "is_checked_in": current_attendance is not None
            and current_attendance.check_out is None,
            "recent_attendances": recent_attendances,
            "today_hours_h": today_hours_h,
            "today_hours_m": today_hours_m,
        }

        return render(request, self.template_name, context)


class AttendanceCheckInView(LoginRequiredMixin, View):
    """View for checking in"""

    def post(self, request):
        employee = request.user.employee

        try:
            # Use model method (handles validations)
            attendance = Attendance.create_check_in(employee=employee)

            # Determine if late (after 9:00 AM)
            if attendance.check_in.time().hour >= 9:
                attendance.status = "late"
                attendance.save()

            messages.success(
                request,
                f'¡Entrada registrada! Hora: {attendance.check_in.strftime("%H:%M")}',
            )
        except ValidationError as e:
            messages.error(request, str(e))

        return redirect("attendance:my-attendance")


class AttendanceCheckOutView(LoginRequiredMixin, View):
    """View for checking out"""

    def post(self, request):
        employee = request.user.employee
        today = timezone.now().date()

        # Find today's attendance without check-out
        attendance = Attendance.objects.filter(
            employee=employee, check_in__date=today, check_out__isnull=True
        ).first()

        if not attendance:
            messages.warning(
                request,
                "No tienes una entrada registrada hoy o ya has fichado la salida.",
            )
            return redirect("attendance:my-attendance")

        try:
            # Use model method
            attendance.process_check_out()

            messages.success(
                request,
                f"¡Salida registrada! Duración: {attendance.duration_formatted}",
            )
        except ValidationError as e:
            messages.error(request, str(e))

        return redirect("attendance:my-attendance")


class AttendanceHistoryView(LoginRequiredMixin, ListView):
    """Complete attendance history for employee"""

    model = Attendance
    template_name = "attendance/AttendanceHistory.html"
    context_object_name = "attendances"
    paginate_by = 20

    def get_queryset(self):
        queryset = Attendance.objects.filter(
            employee=self.request.user.employee
        ).order_by("-check_in")

        # Apply filters if they exist
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        status = self.request.GET.get("status")

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

        # Filter only current user's attendances
        monthly_attendances = Attendance.objects.filter(
            employee=self.request.user.employee,
            check_in__date__gte=first_day_month,
            check_out__isnull=False,
        )

        # Calculate total hours
        total_hours = timedelta()
        for attendance in monthly_attendances:
            if attendance.check_out:
                total_hours += attendance.duration

        # Convert to hours
        total_hours_decimal = total_hours.total_seconds() / 3600

        context["summary"] = {
            "total_days": monthly_attendances.count(),
            "late_count": monthly_attendances.filter(status="late").count(),
            "absent_count": 0,  # Adjust based on your logic
            "total_hours": round(total_hours_decimal, 1),
        }

        context["today"] = today

        return context


class AttendanceReportView(LoginRequiredMixin, View):
    """View for generating attendance reports"""

    template_name = "attendance/AttendanceReport.html"

    def get(self, request):
        context = {
            "years": range(timezone.now().year - 2, timezone.now().year + 1),
            "current_year": timezone.now().year,
            "recent_reports": [],  # Add logic for saved reports here
        }
        return render(request, self.template_name, context)

    def post(self, request):
        # Implement report generation logic here
        report_type = request.POST.get("report_type")
        format_type = request.POST.get("format")

        # For now just redirects back
        messages.success(request, "Funcionalidad de reportes en desarrollo")
        return redirect("attendance:report")
