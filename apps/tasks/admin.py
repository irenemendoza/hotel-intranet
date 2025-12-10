# apps/tasks/admin.py
from django.contrib import admin
from .models import Task, TaskComment


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'department', 
        'assigned_to', 
        'priority', 
        'status', 
        'due_date', 
        'created_at'
        ]
    list_filter = [
        'department', 
        'priority', 
        'status', 
        'created_at'
        ]
    search_fields = [
        'title', 
        'description'
        ]
    raw_id_fields = [
        'created_by', 
        'assigned_to'
        ]
    readonly_fields = [
        'created_at', 
        'updated_at'
        ]


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = [
        'task', 
        'user', 
        'created_at'
        ]
    list_filter = ['created_at']
    search_fields = [
        'task__title', 
        'comment'
        ]
    raw_id_fields = ['task', 'user']