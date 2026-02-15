from django.urls import path

from .views import (
    AttendanceCheckInView,
    AttendanceCheckOutView,
    AttendanceDashboardView,
    AttendanceHistoryView,
    MyAttendanceView,
)

app_name = "attendance"

urlpatterns = [
    # Dashboard de asistencia general
    path("", AttendanceDashboardView.as_view(), name="dashboard"),
    # Fichaje personal del empleado
    path("myattendance/", MyAttendanceView.as_view(), name="my-attendance"),
    path("checkin/", AttendanceCheckInView.as_view(), name="check-in"),
    path("checkout/", AttendanceCheckOutView.as_view(), name="check-out"),
    # Historial personal
    path("history/", AttendanceHistoryView.as_view(), name="history"),
]
