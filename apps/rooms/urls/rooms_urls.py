from django.urls import path
from apps.rooms.views.rooms_views import (
    RoomDashboardView,
    RoomTypeListView, 
    RoomTypeDetailView,
    RoomTypeCreateView, 
    RoomTypeUpdateView,
    RoomTypeDeleteView,
    RoomListView, 
    RoomDetailView,
    RoomCreateView, 
    RoomUpdateView,
    RoomDeleteView
)

app_name = "rooms"

urlpatterns = [
    path('', RoomDashboardView.as_view(), name="dashboard"),
    path('typelist/', RoomTypeListView.as_view(), name="typelist"),
    path('typecreate/', RoomTypeCreateView.as_view(), name="typecreate"),
    path('list/', RoomListView.as_view(), name="list"),
    path('create/', RoomCreateView.as_view(), name="create"),
    path('type/<pk>/', RoomTypeDetailView.as_view(), name="typedetail"),
    path('typeupdate/<pk>/', RoomTypeUpdateView.as_view(), name="typeupdate"),
    path('typedelete/<pk>/', RoomTypeDeleteView.as_view(), name="typedelete"),
    path('update/<pk>/', RoomUpdateView.as_view(), name="update"),
    path('delete/<pk>/', RoomDeleteView.as_view(), name="delete"),
    path('<pk>/', RoomDetailView.as_view(), name="detail"),
    ]
