# apps/tasks/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse

from .models import Task, TaskComment
from apps.users.models import Department
from django.contrib.auth.models import User


@login_required
def task_list(request):
    """Lista de todas las tareas con filtros"""
    tasks = Task.objects.select_related('department', 'assigned_to', 'created_by').all()
    
    # Filtros
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    department_filter = request.GET.get('department')
    assigned_filter = request.GET.get('assigned')
    search = request.GET.get('search')
    
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    
    if department_filter:
        tasks = tasks.filter(department_id=department_filter)
    
    if assigned_filter == 'me':
        tasks = tasks.filter(assigned_to=request.user)
    elif assigned_filter == 'unassigned':
        tasks = tasks.filter(assigned_to__isnull=True)
    
    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Ordenar por prioridad y fecha
    tasks = tasks.order_by('-priority', 'due_date', '-created_at')
    
    # Contexto
    context = {
        'tasks': tasks,
        'departments': Department.objects.all(),
        'status_choices': Task.StatusChoices.choices,
        'priority_choices': Task.PriorityChoices.choices,
        'current_filters': {
            'status': status_filter,
            'priority': priority_filter,
            'department': department_filter,
            'assigned': assigned_filter,
            'search': search,
        }
    }
    
    return render(request, 'tasks/TasksList.html', context)


@login_required
def task_detail(request, pk):
    """Detalle de una tarea específica"""
    task = get_object_or_404(
        Task.objects.select_related('department', 'assigned_to', 'created_by'),
        pk=pk
    )
    comments = task.comments.select_related('user').order_by('-created_at')
    
    context = {
        'task': task,
        'comments': comments,
    }
    
    return render(request, 'tasks/TaskDetail.html', context)


@login_required
def task_create(request):
    """Crear nueva tarea"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        department_id = request.POST.get('department')
        assigned_to_id = request.POST.get('assigned_to')
        priority = request.POST.get('priority')
        due_date = request.POST.get('due_date')
        notes = request.POST.get('notes', '')
        
        # Validaciones básicas
        if not title or not description or not department_id:
            messages.error(request, 'Por favor completa todos los campos obligatorios.')
            return redirect('tasks:create')
        
        # Crear tarea
        task = Task.objects.create(
            title=title,
            description=description,
            department_id=department_id,
            created_by=request.user,
            assigned_to_id=assigned_to_id if assigned_to_id else None,
            priority=priority,
            due_date=due_date if due_date else None,
            notes=notes
        )
        
        # Manejar archivo adjunto
        if request.FILES.get('attachments'):
            task.attachments = request.FILES['attachments']
            task.save()
        
        messages.success(request, f'Tarea "{task.title}" creada exitosamente.')
        return redirect('tasks:detail', pk=task.pk)
    
    # GET request
    context = {
        'departments': Department.objects.all(),
        'users': User.objects.filter(is_active=True).select_related('profile'),
        'priority_choices': Task.PriorityChoices.choices,
    }
    
    return render(request, 'tasks/TaskForm.html', context)


@login_required
def task_edit(request, pk):
    """Editar tarea existente"""
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        task.title = request.POST.get('title')
        task.description = request.POST.get('description')
        task.department_id = request.POST.get('department')
        task.assigned_to_id = request.POST.get('assigned_to') if request.POST.get('assigned_to') else None
        task.priority = request.POST.get('priority')
        task.status = request.POST.get('status')
        task.due_date = request.POST.get('due_date') if request.POST.get('due_date') else None
        task.notes = request.POST.get('notes', '')
        
        # Manejar archivo adjunto
        if request.FILES.get('attachments'):
            task.attachments = request.FILES['attachments']
        
        # Si se marca como completada, registrar fecha
        if task.status == 'completed' and not task.completed_at:
            task.completed_at = timezone.now()
        
        task.save()
        
        messages.success(request, f'Tarea "{task.title}" actualizada exitosamente.')
        return redirect('tasks:detail', pk=task.pk)
    
    context = {
        'task': task,
        'departments': Department.objects.all(),
        'users': User.objects.filter(is_active=True).select_related('profile'),
        'priority_choices': Task.PriorityChoices.choices,
        'status_choices': Task.StatusChoices.choices,
        'is_edit': True,
    }
    
    return render(request, 'tasks/TaskForm.html', context)


@login_required
def task_delete(request, pk):
    """Eliminar tarea"""
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Tarea "{title}" eliminada exitosamente.')
        return redirect('tasks:list')
    
    return render(request, 'tasks/TaskDelete.html', {'task': task})


@login_required
def task_update_status(request, pk):
    """Actualizar estado de tarea (AJAX)"""
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in dict(Task.StatusChoices.choices):
            task.status = new_status
            
            if new_status == 'completed':
                task.completed_at = timezone.now()
            
            task.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Estado actualizado a {task.get_status_display()}'
            })
        
        return JsonResponse({
            'success': False,
            'message': 'Estado inválido'
        }, status=400)
    
    return JsonResponse({'success': False}, status=405)


@login_required
def task_add_comment(request, pk):
    """Agregar comentario a tarea"""
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=pk)
        comment_text = request.POST.get('comment')
        
        if comment_text:
            TaskComment.objects.create(
                task=task,
                user=request.user,
                comment=comment_text
            )
            messages.success(request, 'Comentario agregado.')
        else:
            messages.error(request, 'El comentario no puede estar vacío.')
        
        return redirect('tasks:detail', pk=pk)
    
    return redirect('tasks:list')