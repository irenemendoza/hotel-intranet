from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'check_in', 'check_out', 'status', 'created_at']
    list_filter = ['status', 'check_in']
    search_fields = ['employee__user__first_name', 'employee__user__last_name']
    date_hierarchy = 'check_in'
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Empleado', {
            'fields': ('employee',)
        }),
        ('Horario', {
            'fields': ('check_in', 'check_out', 'status')
        }),
        ('Información Adicional', {
            'fields': ('notes', 'created_at'),
            'classes': ('collapse',)
        }),
    )