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
    path('myattendance/', MyAttendanceView.as_view(), name='my-attendance'),
    path('checkin/', AttendanceCheckInView.as_view(), name='check-in'),
    path('checkout/', AttendanceCheckOutView.as_view(), name='check-out'),
    path('history/', AttendanceHistoryView.as_view(), name='history'),
    
    # Reportes (para RRHH/supervisores)
    path('report/', AttendanceReportView.as_view(), name='report'),
    
    # Leave estáticas
    path('leave/', LeaveListView.as_view(), name='leave-list'),
    path('leave/create/', LeaveCreateView.as_view(), name='leave-create'),
    path('leave/management/', LeaveManagementView.as_view(), name='leave-management'),
    
    
    # Leave dinámicas
    
    path('leave/<int:pk>/', LeaveDetailView.as_view(), name='leave-detail'),
    path('leave/<int:pk>/approval/', LeaveApprovalView.as_view(), name='leave-approval'),
]