from django.urls import path
from apps.employees.views.employees_views import (
    EmployeeListView,
    EmployeeDetailView,
    EmployeeCreateView,
    EmployeeUpdateView,
    EmployeeDeleteView,
    MyTeamView,
)

app_name = 'employees'

urlpatterns = [
    path('', EmployeeListView.as_view(), name='list'),
    path('crear/', EmployeeCreateView.as_view(), name='create'),
    path('<int:pk>/', EmployeeDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', EmployeeUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', EmployeeDeleteView.as_view(), name='delete'),
    path('miequipo/', MyTeamView.as_view(), name='myteam'),
]