from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.rooms.models import MaintenanceTask
from apps.rooms.forms import MaintenanceRequestForm, MaintenanceRequestUpdateForm


class MaintenanceRequestListView(LoginRequiredMixin, ListView):
    model = MaintenanceTask
    template_name = 'rooms/maintenance/RoomMaintenanceList.html'
    context_object_name = 'requests'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('room', 'reported_by', 'assigned_to')
        
        # Filtros
        status = self.request.GET.get('status')
        priority = self.request.GET.get('priority')
        assigned_to = self.request.GET.get('assigned_to')
        
        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        
        return queryset.order_by('-priority', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas
        all_requests = MaintenanceTask.objects.all()
        context['stats'] = {
            'pending': all_requests.filter(status=MaintenanceTask.StatusChoices.PENDING).count(),
            'in_progress': all_requests.filter(status=MaintenanceTask.StatusChoices.IN_PROGRESS).count(),
            'urgent': all_requests.filter(priority=MaintenanceTask.PriorityChoices.URGENT).count(),
        }
        
        context['status_choices'] = MaintenanceTask.StatusChoices.choices
        context['priority_choices'] = MaintenanceTask.PriorityChoices.choices
        
        return context


class MaintenanceRequestDetailView(LoginRequiredMixin, DetailView):
    model = MaintenanceTask
    template_name = 'rooms/maintenance/RoomMaintenanceDetail.html'
    context_object_name = 'request'


class MaintenanceRequestCreateView(LoginRequiredMixin, CreateView):
    model = MaintenanceTask
    form_class = MaintenanceRequestForm
    template_name = 'rooms/maintenance/RoomMaintenanceForm.html'
    success_url = reverse_lazy('maintenance:list')
    
    def form_valid(self, form):
        # Guardar con el usuario actual
        instance = form.save(user=self.request.user)
        messages.success(
            self.request, 
            f'Solicitud de mantenimiento para habitación {instance.room.number} creada correctamente.'
        )
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        # Debug: mostrar errores en la consola
        print("ERRORES DEL FORMULARIO:", form.errors)
        messages.error(
            self.request,
            'Error al crear la solicitud. Por favor, revisa los campos marcados.'
        )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Solicitud de Mantenimiento'
        context['button_text'] = 'Crear Solicitud'
        return context


class MaintenanceRequestUpdateView(LoginRequiredMixin, UpdateView):
    model = MaintenanceTask
    form_class = MaintenanceRequestUpdateForm
    template_name = 'rooms/maintenance/RoomMaintenanceForm.html'
    success_url = reverse_lazy('maintenance:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Solicitud de mantenimiento actualizada correctamente.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        print("ERRORES DEL FORMULARIO:", form.errors)
        messages.error(
            self.request,
            'Error al actualizar la solicitud. Por favor, revisa los campos marcados.'
        )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Mantenimiento'
        context['button_text'] = 'Actualizar'
        return context


class MaintenanceRequestDeleteView(LoginRequiredMixin, DeleteView):
    model = MaintenanceTask
    template_name = 'rooms/maintenance/RoomMaintenanceDelete.html'
    context_object_name = 'request'
    success_url = reverse_lazy('maintenance:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Solicitud de mantenimiento eliminada correctamente.')
        return super().delete(request, *args, **kwargs)


class MyMaintenanceTasksView(LoginRequiredMixin, ListView):
    """Vista para que el personal de mantenimiento vea sus tareas asignadas"""
    model = MaintenanceTask
    template_name = 'rooms/maintenance/MyMaintenanceTasks.html'
    context_object_name = 'requests'
    
    def get_queryset(self):
        return MaintenanceTask.objects.filter(
            assigned_to=self.request.user,
            status__in=[
                MaintenanceTask.StatusChoices.ASSIGNED,
                MaintenanceTask.StatusChoices.IN_PROGRESS
            ]
        ).select_related('room', 'reported_by').order_by('-priority', 'created_at')