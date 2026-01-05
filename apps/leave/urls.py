from django.urls import path
from .views import (
    LeaveListView,
    LeaveCreateView,
    LeaveDetailView,
    LeaveManagementView,
    LeaveApprovalView,
    LeaveUpdateView
)

app_name = 'leave'

urlpatterns = [
    
    path('', LeaveListView.as_view(), name='list'),
    path('create/', LeaveCreateView.as_view(), name='create'),
    path('management/', LeaveManagementView.as_view(), name='management'),
    
    
    # Leave dinámicas
    
    path('<int:pk>/', LeaveDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', LeaveUpdateView.as_view(), name='update'),
    path('<int:pk>/approval/', LeaveApprovalView.as_view(), name='approval'),
]