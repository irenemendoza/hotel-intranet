from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.utils import timezone

from .models import CleaningTask
from .forms import (
    CleaningTaskForm, CleaningTaskUpdateForm
)


class CleaningTaskListView(LoginRequiredMixin, ListView):
    model = CleaningTask
    template_name = 'rooms/cleaning/RoomCleaningList.html'
    context_object_name = 'tasks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('room', 'assigned_to', 'room__room_type')
        
        # Filtros
        status = self.request.GET.get('status')
        cleaning_type = self.request.GET.get('cleaning_type')
        assigned_to = self.request.GET.get('assigned_to')
        date = self.request.GET.get('date')
        
        if status:
            queryset = queryset.filter(status=status)
        if cleaning_type:
            queryset = queryset.filter(cleaning_type=cleaning_type)
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        if date:
            queryset = queryset.filter(scheduled_time__date=date)
        
        return queryset.order_by('-scheduled_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas
        all_tasks = CleaningTask.objects.all()
        context['stats'] = {
            'pending': all_tasks.filter(status=CleaningTask.StatusChoices.PENDING).count(),
            'in_progress': all_tasks.filter(status=CleaningTask.StatusChoices.IN_PROGRESS).count(),
            'completed_today': all_tasks.filter(
                status=CleaningTask.StatusChoices.COMPLETED,
                completed_at__date=timezone.now().date()
            ).count(),
        }
        
        context['status_choices'] = CleaningTask.StatusChoices.choices
        context['type_choices'] = CleaningTask.TypeChoices.choices
        
        return context


class CleaningTaskDetailView(LoginRequiredMixin, DetailView):
    model = CleaningTask
    template_name = 'rooms/cleaning/RoomCleaningDetail.html'
    context_object_name = 'task'


class CleaningTaskCreateView(LoginRequiredMixin, CreateView):
    model = CleaningTask
    form_class = CleaningTaskForm
    template_name = 'rooms/cleaning/RoomCleaningForm.html'
    success_url = reverse_lazy('rooms:cleaning_list')
    
    def form_valid(self, form):
        # Actualizar el estado de la habitación
        room = form.instance.room
        if room.status == Room.StatusChoices.CLEAN:
            room.status = Room.StatusChoices.DIRTY
            room.save()
        
        messages.success(self.request, f'Tarea de limpieza para habitación {form.instance.room.number} creada.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Tarea de Limpieza'
        context['button_text'] = 'Crear'
        return context


class CleaningTaskUpdateView(LoginRequiredMixin, UpdateView):
    model = CleaningTask
    form_class = CleaningTaskUpdateForm
    template_name = 'rooms/cleaning/RoomCleaningForm.html'
    success_url = reverse_lazy('rooms:cleaning_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tarea de limpieza actualizada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Estado de Limpieza'
        return context


class CleaningTaskDeleteView(LoginRequiredMixin, DeleteView):
    model = CleaningTask
    template_name = 'rooms/cleaning/RoomCleaningDelete.html'
    context_object_name = 'task'
    success_url = reverse_lazy('rooms:cleaning_list')
    
    def delete(self, request, *args, **kwargs):
        task = self.get_object()
        messages.success(request, f'Tarea de limpieza eliminada.')
        return super().delete(request, *args, **kwargs)


class MyCleaningTasksView(LoginRequiredMixin, ListView):
    """Vista para que el personal de limpieza vea sus tareas asignadas"""
    model = CleaningTask
    template_name = 'rooms/MyCleaningTasks.html'
    context_object_name = 'tasks'
    
    def get_queryset(self):
        return CleaningTask.objects.filter(
            assigned_to=self.request.user,
            status__in=[CleaningTask.StatusChoices.PENDING, CleaningTask.StatusChoices.IN_PROGRESS]
        ).select_related('room', 'room__room_type').order_by('priority', 'scheduled_time')


