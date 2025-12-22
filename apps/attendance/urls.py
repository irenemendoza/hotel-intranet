from django.urls import path
from .views import (
    AttendanceDashboardView,
    MyAttendanceView,
    AttendanceCheckInView,
    AttendanceCheckOutView,
    AttendanceHistoryView,
    AttendanceReportView,
)

app_name = 'attendance'

urlpatterns = [
    # Dashboard de asistencia general
    path('', AttendanceDashboardView.as_view(), name='dashboard'),
    
    # Fichaje personal del empleado
    path('myattendance/', MyAttendanceView.as_view(), name='my-attendance'),
    path('checkin/', AttendanceCheckInView.as_view(), name='check-in'),
    path('checkout/', AttendanceCheckOutView.as_view(), name='check-out'),

    # Historial personal
    path('history/', AttendanceHistoryView.as_view(), name='history'),
    
    # Reportes (para RRHH/supervisores)
    path('report/', AttendanceReportView.as_view(), name='report'),
]