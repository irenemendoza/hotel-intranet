from django.contrib import admin
from .models import Leave

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'status', 'created_at']
    list_filter = ['status', 'leave_type', 'start_date']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'reason']
    date_hierarchy = 'start_date'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Empleado', {
            'fields': ('employee',)
        }),
        ('Detalles del Permiso', {
            'fields': ('leave_type', 'start_date', 'end_date', 'reason', 'attachment')
        }),
        ('Estado', {
            'fields': ('status', 'approved_by', 'approved_at', 'rejection_reason')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != 'pending':
            return self.readonly_fields + ('employee', 'leave_type', 'start_date', 'end_date')
        return self.readonly_fields