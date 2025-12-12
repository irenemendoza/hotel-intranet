from django.shortcuts import render

# Create your views here.

from django.shortcuts import render
from apps.rooms.models import Room

from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView


class RoomListView(ListView):
    model = Room
    template_name = "rooms/RoomList.html"
    context_object_name = "rooms"


class RoomDetailView(DetailView):
    model = Department
    template_name = "rooms/RoomDetail.html"
    context_object_name = "room"


class RoomUpdateView(UpdateView):
    model = Room
    fields = ["status", "occupancy", "last_cleaned", "last_inspected", "notes", "is_active"]
    template_name = "rooms/RoomUpdate.html"
    context_object_name = "room"

