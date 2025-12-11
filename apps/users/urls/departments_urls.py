from django.urls import path
from apps.users.views import (
DepartmentListView, 
DepartmentDetailView, 
DepartmentCreateView,
DepartmentUpdateView,
DepartmentDeleteView
)

app_name = "departments"

urlpatterns = [
    path('list/', DepartmentListView.as_view(), name="list"),
    path('create/', DepartmentCreateView.as_view(), name="create"),
    path('<pk>/', DepartmentDetailView.as_view(), name="detail"),
    path('update/<pk>', DepartmentUpdateView.as_view(), name="update"),
    path('delete/<pk>', DepartmentDeleteView.as_view(), name="delete"),
    ]