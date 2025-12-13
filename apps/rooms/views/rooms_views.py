from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, Case, When, IntegerField
from django.utils import timezone
from django.http import JsonResponse

from .models import Room, RoomType, CleaningTask, MaintenanceRequest
from .forms import (
    RoomForm, RoomTypeForm, CleaningTaskForm, CleaningTaskUpdateForm,
    MaintenanceRequestForm, MaintenanceRequestUpdateForm
)


# ==================== DASHBOARD ====================

class RoomsDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal de habitaciones con vista de pisos"""
    template_name = 'rooms/RoomDashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener todas las habitaciones activas agrupadas por piso
        rooms = Room.objects.filter(is_active=True).select_related('room_type').order_by('floor', 'number')
        
        # Agrupar por piso
        floors = {}
        for room in rooms:
            if room.floor not in floors:
                floors[room.floor] = []
            floors[room.floor].append(room)
        
        context['floors'] = dict(sorted(floors.items(), reverse=True))
        
        # Estadísticas generales
        total_rooms = rooms.count()
        context['stats'] = {
            'total': total_rooms,
            'vacant': rooms.filter(occupancy=Room.OccupancyChoices.VACANT).count(),
            'occupied': rooms.filter(occupancy=Room.OccupancyChoices.OCCUPIED).count(),
            'reserved': rooms.filter(occupancy=Room.OccupancyChoices.RESERVED).count(),
            'clean': rooms.filter(status=Room.StatusChoices.CLEAN).count(),
            'dirty': rooms.filter(status=Room.StatusChoices.DIRTY).count(),
            'maintenance': rooms.filter(status=Room.StatusChoices.MAINTENANCE).count(),
        }
        
        # Calcular porcentajes
        if total_rooms > 0:
            context['stats']['occupancy_rate'] = round((context['stats']['occupied'] / total_rooms) * 100, 1)
            context['stats']['clean_rate'] = round((context['stats']['clean'] / total_rooms) * 100, 1)
        else:
            context['stats']['occupancy_rate'] = 0
            context['stats']['clean_rate'] = 0
        
        # Tareas pendientes
        context['pending_cleanings'] = CleaningTask.objects.filter(
            status__in=[CleaningTask.StatusChoices.PENDING, CleaningTask.StatusChoices.IN_PROGRESS]
        ).select_related('room', 'assigned_to').order_by('priority', 'scheduled_time')[:5]
        
        context['pending_maintenance'] = MaintenanceRequest.objects.filter(
            status__in=[MaintenanceRequest.StatusChoices.PENDING, MaintenanceRequest.StatusChoices.ASSIGNED]
        ).select_related('room', 'reported_by').order_by('-priority', 'created_at')[:5]
        
        return context


# ==================== ROOM TYPE CRUD ====================

class RoomTypeListView(LoginRequiredMixin, ListView):
    model = RoomType
    template_name = 'rooms/type/RoomtypeList.html'
    context_object_name = 'room_types'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Anotar con el número de habitaciones de cada tipo
        return queryset.annotate(room_count=Count('room'))


class RoomTypeDetailView(LoginRequiredMixin, DetailView):
    model = RoomType
    template_name = 'rooms/type/RoomTypeDetail.html'
    context_object_name = 'room_type'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rooms'] = self.object.room_set.filter(is_active=True)
        return context


class RoomTypeCreateView(LoginRequiredMixin, CreateView):
    model = RoomType
    form_class = RoomTypeForm
    template_name = 'rooms/type/RoomTypeForm.html'
    success_url = reverse_lazy('rooms:roomtype_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Tipo de habitación "{form.instance.name}" creado exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Tipo de Habitación'
        context['button_text'] = 'Crear'
        return context


class RoomTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = RoomType
    form_class = RoomTypeForm
    template_name = 'rooms/type/RoomTypeForm.html'
    success_url = reverse_lazy('rooms:roomtype_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Tipo de habitación "{form.instance.name}" actualizado exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Tipo de Habitación'
        context['button_text'] = 'Actualizar'
        return context


class RoomTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = RoomType
    template_name = 'rooms/type/RoomTypeDelete.html'
    context_object_name = 'room_type'
    success_url = reverse_lazy('rooms:roomtype_list')
    
    def delete(self, request, *args, **kwargs):
        room_type = self.get_object()
        # Verificar si hay habitaciones asociadas
        if room_type.room_set.exists():
            messages.error(
                request, 
                f'No se puede eliminar "{room_type.name}" porque tiene habitaciones asociadas.'
            )
            return redirect('rooms:roomtype_detail', pk=room_type.pk)
        
        messages.success(request, f'Tipo de habitación "{room_type.name}" eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)


# ==================== ROOM CRUD ====================

class RoomListView(LoginRequiredMixin, ListView):
    model = Room
    template_name = 'rooms/RoomList.html'
    context_object_name = 'rooms'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('room_type')
        
        # Filtros
        status = self.request.GET.get('status')
        occupancy = self.request.GET.get('occupancy')
        floor = self.request.GET.get('floor')
        room_type = self.request.GET.get('room_type')
        search = self.request.GET.get('search')
        
        if status:
            queryset = queryset.filter(status=status)
        if occupancy:
            queryset = queryset.filter(occupancy=occupancy)
        if floor:
            queryset = queryset.filter(floor=floor)
        if room_type:
            queryset = queryset.filter(room_type_id=room_type)
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) | 
                Q(room_type__name__icontains=search)
            )
        
        return queryset.order_by('floor', 'number')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room_types'] = RoomType.objects.filter(is_active=True)
        context['floors'] = Room.objects.values_list('floor', flat=True).distinct().order_by('floor')
        context['status_choices'] = Room.StatusChoices.choices
        context['occupancy_choices'] = Room.OccupancyChoices.choices
        return context


class RoomDetailView(LoginRequiredMixin, DetailView):
    model = Room
    template_name = 'rooms/RoomDetail.html'
    context_object_name = 'room'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Historial de limpieza
        context['cleaning_history'] = self.object.cleaning_tasks.all().order_by('-created_at')[:10]
        
        # Solicitudes de mantenimiento
        context['maintenance_history'] = self.object.maintenance_requests.all().order_by('-created_at')[:10]
        
        # Tarea de limpieza pendiente
        context['pending_cleaning'] = self.object.cleaning_tasks.filter(
            status__in=[CleaningTask.StatusChoices.PENDING, CleaningTask.StatusChoices.IN_PROGRESS]
        ).first()
        
        # Mantenimiento pendiente
        context['pending_maintenance'] = self.object.maintenance_requests.filter(
            status__in=[MaintenanceRequest.StatusChoices.PENDING, 
                       MaintenanceRequest.StatusChoices.ASSIGNED,
                       MaintenanceRequest.StatusChoices.IN_PROGRESS]
        ).order_by('-priority', 'created_at')
        
        return context


class RoomCreateView(LoginRequiredMixin, CreateView):
    model = Room
    form_class = RoomForm
    template_name = 'rooms/RoomForm.html'
    success_url = reverse_lazy('rooms:room_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Habitación {form.instance.number} creada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Habitación'
        context['button_text'] = 'Crear'
        return context


class RoomUpdateView(LoginRequiredMixin, UpdateView):
    model = Room
    form_class = RoomForm
    template_name = 'rooms/RoomForm.html'
    
    def get_success_url(self):
        return reverse_lazy('rooms:room_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Habitación {form.instance.number} actualizada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Habitación'
        context['button_text'] = 'Actualizar'
        return context


class RoomDeleteView(LoginRequiredMixin, DeleteView):
    model = Room
    template_name = 'rooms/RoomDelete.html'
    context_object_name = 'room'
    success_url = reverse_lazy('rooms:room_list')
    
    def delete(self, request, *args, **kwargs):
        room = self.get_object()
        messages.success(request, f'Habitación {room.number} eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)


# ==================== CLEANING TASKS ====================

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


# ==================== MAINTENANCE REQUESTS ====================

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


# ==================== VISTAS ADICIONALES ====================

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