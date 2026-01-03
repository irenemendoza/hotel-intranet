# apps/dashboard/urls.py
from django.urls import path
from .views import DashboardView, MyTasksView

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardView.as_view(), name='home'),
    path('tareas/', MyTasksView.as_view(), name='tasks'),
]