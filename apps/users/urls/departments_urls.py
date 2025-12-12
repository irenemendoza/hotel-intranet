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
    path('departments/create/', DepartmentCreateView.as_view(), name="create"),
    path('departments/<pk>/', DepartmentDetailView.as_view(), name="detail"),
    path('departments/update/<pk>', DepartmentUpdateView.as_view(), name="update"),
    path('departments/delete/<pk>', DepartmentDeleteView.as_view(), name="delete"),
    ]