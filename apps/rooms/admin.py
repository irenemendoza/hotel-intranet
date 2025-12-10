# apps/rooms/admin.py
from django.contrib import admin
from .models import RoomType, Room, CleaningTask, MaintenanceRequest


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'code', 
        'capacity', 
        'base_price', 
        'is_active'
        ]
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = [
        'number', 
        'floor', 
        'room_type', 
        'status', 
        'occupancy', 
        'last_cleaned'
        ]
    list_filter = [
        'floor', 
        'room_type', 
        'status', 
        'occupancy', 
        'is_active'
        ]
    search_fields = ['number']
    readonly_fields = [
        'created_at', 
        'updated_at'
        ]


@admin.register(CleaningTask)
class CleaningTaskAdmin(admin.ModelAdmin):
    list_display = [
        'room', 
        'assigned_to', 
        'cleaning_type', 
        'status', 
        'priority', 
        'scheduled_time'
        ]
    list_filter = [
        'status', 
        'cleaning_type', 
        'priority'
        ]
    search_fields = ['room__number']
    raw_id_fields = [
        'room', 
        'assigned_to', 
        'verified_by'
        ]


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = [
        'room', 
        'title', 
        'priority', 
        'status', 
        'reported_by', 
        'assigned_to', 
        'created_at'
        ]
    list_filter = [
        'priority', 
        'status', 
        'created_at'
        ]
    search_fields = [
        'room__number', 
        'title', 
        'description'
        ]
    raw_id_fields = [
        'room', 
        'reported_by', 
        'assigned_to'
        ]