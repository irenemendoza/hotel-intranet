from django.urls import path
from apps.rooms.views.rooms_maintenance_views import (
    MaintenanceRequestListView,
    MaintenanceRequestDetailView,
    MaintenanceRequestCreateView,
    MaintenanceRequestUpdateView,
    MaintenanceRequestDeleteView,
    MyMaintenanceTasksView
)

app_name = "maintenance"

urlpatterns = [
    path('list/', MaintenanceRequestListView.as_view(), name="list"),
    path('create/', MaintenanceRequestCreateView.as_view(), name="create"),
    path('mymaintenancetasks/', MyMaintenanceTasksView.as_view(), name="tasks"),
    path('update/<pk>/', MaintenanceRequestUpdateView.as_view(), name="update"),
    path('delete/<pk>/', MaintenanceRequestDeleteView.as_view(), name="delete"),
    path('<pk>/', MaintenanceRequestDetailView.as_view(), name="detail"),
]
