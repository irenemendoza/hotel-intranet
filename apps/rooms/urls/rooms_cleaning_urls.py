from django.urls import path
from apps.rooms.views.rooms_cleaning_views import (
    CleaningTaskListView, 
    CleaningTaskDetailView,
    CleaningTaskCreateView, 
    CleaningTaskUpdateView,
    CleaningTaskDeleteView,
    MyCleaningTasksView
)


urlpatterns = [
    path('list/', CleaningTaskListView.as_view(), name="cleaning-list"),
    path('create/', CleaningTaskCreateView.as_view(), name="cleaning-create"),
    path('mycleaningtasks/',MyCleaningTasksView.as_view(), name="cleaning-tasks"),
    path('update/<pk>/', CleaningTaskUpdateView.as_view(), name="cleaning-update"),
    path('delete/<pk>/', CleaningTaskDeleteView.as_view(), name="cleaning-delete"),
    path('<pk>/', CleaningTaskDetailView.as_view(), name="cleaning-detail"),
    ]
