from django.urls import path
from apps.rooms.views.rooms_cleaning_views import (
    CleaningTaskListView, 
    CleaningTaskDetailView,
    CleaningTaskCreateView, 
    CleaningTaskUpdateView,
    CleaningTaskDeleteView,
    MyCleaningTasksView
)

app_name = "cleaning"

urlpatterns = [
    path('list/', CleaningTaskListView.as_view(), name="list"),
    path('create/', CleaningTaskCreateView.as_view(), name="create"),
    path('mycleaningtasks/',MyCleaningTasksView.as_view(), name="tasks"),
    path('update/<pk>/', CleaningTaskUpdateView.as_view(), name="update"),
    path('delete/<pk>/', CleaningTaskDeleteView.as_view(), name="delete"),
    path('<pk>/', CleaningTaskDetailView.as_view(), name="detail"),
    ]
