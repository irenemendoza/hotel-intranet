

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView

from apps.employees.models import Employee

from apps.rooms.models import Room, RoomType, Reservation
from apps.rooms.forms import RoomForm, RoomTypeForm
from apps.rooms.models import CleaningTask, MaintenanceTask



# ==================== DASHBOARD ====================

class RoomDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal de habitaciones con vista de pisos"""
    template_name = 'rooms/type/RoomDashboard.html'
    
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
        ).select_related('room', 'assigned_to').order_by('priority')[:5]
        
        context['pending_maintenance'] = MaintenanceTask.objects.filter(
            status__in=[MaintenanceTask.StatusChoices.PENDING, MaintenanceTask.StatusChoices.ASSIGNED]
        ).select_related('room', 'reported_by').order_by('-priority', 'created_at')[:5]
        
        return context


# ==================== ROOM TYPE CRUD ====================

class RoomTypeListView(LoginRequiredMixin, ListView):
    model = RoomType
    template_name = 'rooms/type/RoomTypeList.html'
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
        context['rooms'] = Room.objects.filter(room_type=self.object)
        return context


class RoomTypeCreateView(LoginRequiredMixin, CreateView):
    model = RoomType
    form_class = RoomTypeForm
    template_name = 'rooms/type/RoomTypeForm.html'
    success_url = reverse_lazy('rooms:typelist')
    
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
    success_url = reverse_lazy('rooms:typelist')
    
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
    success_url = reverse_lazy('rooms:typelist')
    
    def delete(self, request, *args, **kwargs):
        room_type = self.get_object()
        # Verificar si hay habitaciones asociadas
        if room_type.room_set.exists():
            messages.error(
                request, 
                f'No se puede eliminar "{room_type.name}" porque tiene habitaciones asociadas.'
            )
            return redirect('rooms:typedetail', pk=room_type.pk)
        
        messages.success(request, f'Tipo de habitación "{room_type.name}" eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)


# ==================== ROOM CRUD ====================

class RoomListView(LoginRequiredMixin, ListView):
    model = Room
    template_name = 'rooms/type/RoomList.html'
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
    template_name = 'rooms/type/RoomDetail.html'
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
            status__in=[MaintenanceTask.StatusChoices.PENDING, 
                       MaintenanceTask.StatusChoices.ASSIGNED,
                       MaintenanceTask.StatusChoices.IN_PROGRESS]
        ).order_by('-priority', 'created_at')
        
        return context


class RoomCreateView(LoginRequiredMixin, CreateView):
    model = Room
    form_class = RoomForm
    template_name = 'rooms/type/RoomForm.html'
    success_url = reverse_lazy('rooms:list')
    
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
    template_name = 'rooms/type/RoomForm.html'
    
    def get_success_url(self):
        return reverse_lazy('rooms:detail', kwargs={'pk': self.object.pk})
    
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
    template_name = 'rooms/type/RoomDelete.html'
    context_object_name = 'room'
    success_url = reverse_lazy('rooms:list')
    
    def delete(self, request, *args, **kwargs):
        room = self.get_object()
        messages.success(request, f'Habitación {room.number} eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)




