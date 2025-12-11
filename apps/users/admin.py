# apps/users/admin.py
from django.contrib import admin
from .models import Department, UserProfile

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

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'department', 
        'position', 
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