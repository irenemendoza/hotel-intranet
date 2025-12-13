from django.urls import path
from apps.rooms.views.rooms_maintenance_views import (
    MaintenanceTaskDetailView,
    MaintenanceTaskCreateView, 
    MaintenanceTaskUpdateView,
    MaintenanceTaskDeleteView,
    MyMaintenanceTasksView
)


urlpatterns = [
    path('list/', MaintenanceTaskListView.as_view(), name="maintenance-list"),
    path('<pk>/', MaintenanceTaskDetailView.as_view(), name="maintenance-detail"),
    path('create/', MaintenanceTaskCreate.as_view(), name="maintenance-create"),
    path('update/<pk>', MaintenanceTaskUpdateView.as_view(), name="maintenance-update"),
    path('delete/', MaintenanceTaskDeleteView.as_view(), name="maintenance-delete"),
    path('mymaintenancetasks/',MyMaintenanceTasksView.as_view(), name="maintenance-tasks"),
    ]
