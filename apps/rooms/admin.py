# apps/rooms/admin.py
from django.contrib import admin
from .models import RoomType, Room, CleaningTask, MaintenanceTask, Reservation


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'code', 
        'capacity', 
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

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    search_fields = (
        'reservation_number',
        'guest_first_name',
        'guest_last_name',
        'guest_email',
        'guest_phone',
        'guest_dni',
    )

    readonly_fields = (
        'reservation_number',
        'total_amount',
        'pending_amount_display',
        'created_at',
        'updated_at',
    )

    date_hierarchy = 'check_in_date'

    list_display = (
        'reservation_number',
        'guest_full_name',
        'room',
        'check_in_date',
        'check_out_date',
        'payment_status',
        'total_amount',
    )

    list_filter = (
        'status',
        'payment_status',
        'check_in_date',
        'check_out_date',
    )


@admin.register(CleaningTask)
class CleaningTaskAdmin(admin.ModelAdmin):
    list_display = [
        'room', 
        'assigned_to', 
        'cleaning_type', 
        'status', 
        'priority', 
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


@admin.register(MaintenanceTask)
class MaintenanceTaskAdmin(admin.ModelAdmin):
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