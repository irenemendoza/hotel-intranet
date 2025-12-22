# apps/employees/admin.py
from django.contrib import admin
from .models import Department, Employee

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'code',
        'color',  
        'is_active', 
        'created_at'
        ]
    list_filter = [
        'is_active'
        ]
    search_fields = [
        'name', 
        'code'
        ]

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'department', 
        'role', 
        'phone', 
        'is_available'
        ]
    list_filter = [
        'department', 
        'is_available'
        ]
    search_fields = [
        'user__username', 
        'user__first_name', 
        'user__last_name', 
        'employee_number'
        ]
    raw_id_fields = [
        'user'
        ]