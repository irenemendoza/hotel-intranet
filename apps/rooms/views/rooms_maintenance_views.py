from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.utils import timezone
from django.http import JsonResponse

from apps.rooms.models import MaintenanceRequest
from apps.forms.rooms_forms import (
    MaintenanceRequestForm, MaintenanceRequestUpdateForm
)


class MaintenanceRequestListView(LoginRequiredMixin, ListView):
    model = MaintenanceRequest
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
        all_requests = MaintenanceRequest.objects.all()
        context['stats'] = {
            'pending': all_requests.filter(status=MaintenanceRequest.StatusChoices.PENDING).count(),
            'in_progress': all_requests.filter(status=MaintenanceRequest.StatusChoices.IN_PROGRESS).count(),
            'urgent': all_requests.filter(priority=MaintenanceRequest.PriorityChoices.URGENT).count(),
        }
        
        context['status_choices'] = MaintenanceRequest.StatusChoices.choices
        context['priority_choices'] = MaintenanceRequest.PriorityChoices.choices
        
        return context


class MaintenanceRequestDetailView(LoginRequiredMixin, DetailView):
    model = MaintenanceRequest
    template_name = 'rooms/maintenance/RoomMaintenanceDetail.html'
    context_object_name = 'request'


class MaintenanceRequestCreateView(LoginRequiredMixin, CreateView):
    model = MaintenanceRequest
    form_class = MaintenanceRequestForm
    template_name = 'rooms/maintenance/RoomMaintenanceForm.html'
    success_url = reverse_lazy('rooms:maintenance_list')
    
    def form_valid(self, form):
        form.save(user=self.request.user)
        messages.success(
            self.request, 
            f'Solicitud de mantenimiento para habitación {form.instance.room.number} creada.'
        )
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Solicitud de Mantenimiento'
        context['button_text'] = 'Crear'
        return context


class MaintenanceRequestUpdateView(LoginRequiredMixin, UpdateView):
    model = MaintenanceRequest
    form_class = MaintenanceRequestUpdateForm
    template_name = 'rooms/maintenance/RoomMaintenanceForm.html'
    success_url = reverse_lazy('rooms:maintenance_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Solicitud de mantenimiento actualizada.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Mantenimiento'
        return context


class MaintenanceRequestDeleteView(LoginRequiredMixin, DeleteView):
    model = MaintenanceRequest
    template_name = 'rooms/maintenance/RoomMaintenanceDelete.html'
    context_object_name = 'request'
    success_url = reverse_lazy('rooms:maintenance_list')
    
    def delete(self, request, *args, **kwargs):
        maintenance = self.get_object()
        messages.success(request, 'Solicitud de mantenimiento eliminada.')
        return super().delete(request, *args, **kwargs)



class MyMaintenanceTasksView(LoginRequiredMixin, ListView):
    """Vista para que el personal de mantenimiento vea sus tareas asignadas"""
    model = MaintenanceRequest
    template_name = 'rooms/MyMaintenanceTasks.html'
    context_object_name = 'requests'
    
    def get_queryset(self):
        return MaintenanceRequest.objects.filter(
            assigned_to=self.request.user,
            status__in=[
                MaintenanceRequest.StatusChoices.ASSIGNED,
                MaintenanceRequest.StatusChoices.IN_PROGRESS
            ]
        ).select_related('room', 'reported_by').order_by('-priority', 'created_at')