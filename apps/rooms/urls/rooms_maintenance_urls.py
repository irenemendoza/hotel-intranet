from django.urls import path
from apps.rooms.views.rooms_maintenance_views import (
    MaintenanceRequestListView,
    MaintenanceRequestDetailView,
    MaintenanceRequestCreateView,
    MaintenanceRequestUpdateView,
    MaintenanceRequestDeleteView,
    MyMaintenanceTasksView
)

urlpatterns = [
    path('list/', MaintenanceRequestListView.as_view(), name="maintenance-list"),
    path('create/', MaintenanceRequestCreateView.as_view(), name="maintenance-create"),
    path('mymaintenancetasks/', MyMaintenanceTasksView.as_view(), name="maintenance-tasks"),
    path('update/<pk>/', MaintenanceRequestUpdateView.as_view(), name="maintenance-update"),
    path('delete/<pk>/', MaintenanceRequestDeleteView.as_view(), name="maintenance-delete"),
    path('<pk>/', MaintenanceRequestDetailView.as_view(), name="maintenance-detail"),
]
