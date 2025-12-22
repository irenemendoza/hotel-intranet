from django.urls import path
from apps.employees.views.employees_views import (
    EmployeeListView,
    EmployeeDetailView,
    EmployeeCreateView,
    EmployeeUpdateView,
    EmployeeDeleteView
)

app_name = 'users'

urlpatterns = [
    path('', EmployeeListView.as_view(), name='list'),
    path('crear/', EmployeeCreateView.as_view(), name='create'),
    path('<int:pk>/', EmployeeDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', EmployeeUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', EmployeeDeleteView.as_view(), name='delete'),
]