from django.urls import path
from apps.users.views import (
RoomListView, 
RoomDetailView, 
RoomUpdateView
)

app_name = "rooms"

urlpatterns = [
    path('list/', RoomListView.as_view(), name="list"),
    path('<pk>/', RoomDetailView.as_view(), name="detail"),
    path('update/<pk>', RoomUpdateView.as_view(), name="update"),
    ]