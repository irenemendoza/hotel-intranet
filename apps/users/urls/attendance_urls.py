from django.urls import path
from ..views.users_views import (
    AttendanceDashboardView,
    MyAttendanceView,
    AttendanceCheckInView,
    AttendanceCheckOutView,
    AttendanceHistoryView,
    AttendanceReportView,
    LeaveListView,
    LeaveCreateView,
    LeaveDetailView,
    LeaveManagementView,
    LeaveApprovalView
)

app_name = 'attendance'

urlpatterns = [
    # Dashboard de asistencia general
    path('', AttendanceDashboardView.as_view(), name='dashboard'),
    
    # Fichaje personal del empleado
    path('mi-fichaje/', MyAttendanceView.as_view(), name='my-attendance'),
    path('fichar-entrada/', AttendanceCheckInView.as_view(), name='check-in'),
    path('fichar-salida/', AttendanceCheckOutView.as_view(), name='check-out'),
    path('mi-historial/', AttendanceHistoryView.as_view(), name='history'),
    
    # Reportes (para RRHH/supervisores)
    path('reporte/', AttendanceReportView.as_view(), name='report'),
    
    # Gestión de permisos/vacaciones
    path('permisos/', LeaveListView.as_view(), name='leave-list'),
    path('permisos/solicitar/', LeaveCreateView.as_view(), name='leave-create'),
    path('permisos/<int:pk>/', LeaveDetailView.as_view(), name='leave-detail'),
    
    # Gestión de permisos (para RRHH/supervisores)
    path('permisos/gestion/', LeaveManagementView.as_view(), name='leave-management'),
    path('permisos/<int:pk>/aprobar/', LeaveApprovalView.as_view(), name='leave-approval'),
]