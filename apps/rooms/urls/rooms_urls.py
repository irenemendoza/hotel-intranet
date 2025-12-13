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


urlpatterns = [
    path('/', RoomDashboardView.as_view(), name="dashboard"),
    path('typelist/', RoomTypeListView.as_view(), name="typelist"),
    path('type/<pk>/', RoomTypeDetailView.as_view(), name="typedetail"),
    path('typecreate/', RoomTypeCreateView.as_view(), name="typecreate"),
    path('typeupdate/<pk>', RoomTypeUpdateView.as_view(), name="typeupdate"),
    path('typedelete/', RoomTypeDeleteView.as_view(), name="typedelete"),
    path('list/', RoomListView.as_view(), name="list"),
    path('<pk>/', RoomDetailView.as_view(), name="detail"),
    path('create/', RoomCreateView.as_view(), name="create"),
    path('update/<pk>', RoomUpdateView.as_view(), name="update"),
    path('delete/', RoomDeleteView.as_view(), name="delete"),
    ]
