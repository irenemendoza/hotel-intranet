# apps/leaves/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Leave
from apps.employees.models import Employee
from .forms import LeaveRequestForm, LeaveApprovalForm


class LeaveListView(LoginRequiredMixin, ListView):
    """Lista de permisos del empleado actual"""
    model = Leave
    template_name = 'leave/LeaveList.html'
    context_object_name = 'leaves'
    paginate_by = 20
    
    def get_queryset(self):
        return Leave.objects.filter(
            employee=self.request.user.employee
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        employee = self.request.user.employee
        
        # Estadísticas personales
        context['available_days'] = 22  # Ajusta según tu lógica
        context['pending_count'] = Leave.objects.filter(
            employee=employee,
            status='pending'
        ).count()
        context['approved_count'] = Leave.objects.filter(
            employee=employee,
            status='approved'
        ).count()
        
        # Calcular días usados
        approved_leaves = Leave.objects.filter(
            employee=employee,
            status='approved'
        )
        used_days = sum(leave.duration_days() for leave in approved_leaves)
        context['used_days'] = used_days
        
        return context


class LeaveCreateView(LoginRequiredMixin, CreateView):
    """Crear una nueva solicitud de permiso"""
    model = Leave
    form_class = LeaveRequestForm
    template_name = 'leave/LeaveForm.html'
    success_url = reverse_lazy('leave:list')
    
    def form_valid(self, form):
        form.instance.employee = self.request.user.employee
        messages.success(self.request, 'Solicitud de permiso enviada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Solicitar Permiso'
        context['button_text'] = 'Enviar Solicitud'
        context['employee'] = self.request.user.employee
        return context


class LeaveDetailView(LoginRequiredMixin, DetailView):
    """Vista de detalle de un permiso"""
    model = Leave
    template_name = 'leave/LeaveDetail.html'
    context_object_name = 'leave'
    
    def get_queryset(self):
        # El usuario puede ver sus propios permisos
        queryset = Leave.objects.all()
        
        # Si no es supervisor, solo ve los suyos
        if not self.request.user.employee.is_supervisor():
            queryset = queryset.filter(employee=self.request.user.employee)
        
        return queryset


class LeaveManagementView(LoginRequiredMixin, ListView):
    """Gestión de permisos para supervisores y RRHH"""
    model = Leave
    template_name = 'leave/LeaveManagement.html'
    context_object_name = 'leaves'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        # Solo supervisores y RRHH pueden acceder
        if not hasattr(request.user, 'employee') or not request.user.employee.is_supervisor():
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        profile = self.request.user.employee
        
        # Obtener parámetros de filtro
        status = self.request.GET.get('status', '')
        leave_type = self.request.GET.get('leave_type', '')
        employee_search = self.request.GET.get('employee', '')
        
        # Dirección y RRHH ven todos los permisos
        if profile.role in ['director', 'rrhh']:
            queryset = Leave.objects.all()
        else:
            # Jefes solo ven los de su equipo
            supervised_employees = profile.get_supervised_employees()
            queryset = Leave.objects.filter(employee__in=supervised_employees)
        
        # Aplicar filtros
        if status:
            queryset = queryset.filter(status=status)
        
        if leave_type:
            queryset = queryset.filter(leave_type=leave_type)
        
        if employee_search:
            queryset = queryset.filter(
                Q(employee__user__first_name__icontains=employee_search) |
                Q(employee__user__last_name__icontains=employee_search)
            )
        
        return queryset.select_related(
            'employee', 
            'employee__user', 
            'employee__department',
            'approved_by'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        profile = self.request.user.employee
        
        # Base queryset según rol
        if profile.role in ['director', 'rrhh']:
            base_queryset = Leave.objects.all()
        else:
            supervised = profile.get_supervised_employees()
            base_queryset = Leave.objects.filter(employee__in=supervised)
        
        # Estadísticas
        context['pending_count'] = base_queryset.filter(status='pending').count()
        context['approved_count'] = base_queryset.filter(status='approved').count()
        context['rejected_count'] = base_queryset.filter(status='rejected').count()
        
        # Total del mes
        today = timezone.now().date()
        first_day_month = today.replace(day=1)
        context['month_total'] = base_queryset.filter(
            created_at__gte=first_day_month
        ).count()
        
        return context


class LeaveApprovalView(LoginRequiredMixin, UpdateView):
    """Vista para aprobar o rechazar un permiso"""
    model = Leave
    form_class = LeaveApprovalForm
    template_name = 'leave/LeaveApproval.html'
    success_url = reverse_lazy('leave:management')
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar que es supervisor
        if not hasattr(request.user, 'employee') or not request.user.employee.is_supervisor():
            messages.error(request, 'No tienes permiso para aprobar permisos.')
            return redirect('dashboard:home')
        
        # Obtener el permiso
        leave = self.get_object()
        
        # Verificar que puede gestionar este permiso
        profile = request.user.employee
        if profile.role not in ['director', 'rrhh']:
            # Los jefes solo pueden aprobar permisos de su equipo
            supervised = profile.get_supervised_employees()
            if leave.employee not in supervised:
                messages.error(request, 'No puedes aprobar este permiso.')
                return redirect('leave:management')
        
        # Verificar que el permiso está pendiente
        if leave.status != 'pending':
            messages.warning(request, 'Este permiso ya ha sido procesado.')
            return redirect('leave:detail', pk=leave.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        profile = self.request.user.employee
        
        if profile.role in ['director', 'rrhh']:
            return Leave.objects.all()
        
        # Jefes solo ven los de su equipo
        supervised = profile.get_supervised_employees()
        return Leave.objects.filter(employee__in=supervised)
    
    def form_valid(self, form):
        leave = form.save(commit=False, user=self.request.user)
        
        # Guardar
        leave.save()
        
        # Mensajes
        if leave.status == 'approved':
            messages.success(
                self.request, 
                f'Permiso aprobado para {leave.employee.get_full_name()}'
            )
        elif leave.status == 'rejected':
            messages.warning(
                self.request, 
                f'Permiso rechazado para {leave.employee.get_full_name()}'
            )
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        leave = self.get_object()
        
        # Historial reciente del empleado
        context['recent_leaves'] = Leave.objects.filter(
            employee=leave.employee
        ).exclude(
            pk=leave.pk
        ).order_by('-created_at')[:5]
        
        return context


class LeaveUpdateView(LoginRequiredMixin, UpdateView):
    """Editar un permiso (solo si está pendiente)"""
    model = Leave
    form_class = LeaveRequestForm
    template_name = 'leave/LeaveForm.html'
    
    def get_success_url(self):
        return reverse_lazy('leave:detail', kwargs={'pk': self.object.pk})
    
    def get_queryset(self):
        # Solo puede editar sus propios permisos pendientes
        return Leave.objects.filter(
            employee=self.request.user.employee,
            status='pending'
        )
    
    def dispatch(self, request, *args, **kwargs):
        leave = self.get_object()
        
        if leave.status != 'pending':
            messages.error(request, 'No puedes editar un permiso que ya ha sido procesado.')
            return redirect('leave:detail', pk=leave.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'Permiso actualizado exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Permiso'
        context['button_text'] = 'Actualizar'
        context['employee'] = self.request.user.employee
        return context

"""
class LeaveCancelView(LoginRequiredMixin, UpdateView):
    # Cancelar un permiso pendiente
    model = Leave
    fields = []
    template_name = 'leave/leave_confirm_cancel.html'
    
    def get_queryset(self):
        # Solo puede cancelar sus propios permisos pendientes
        return Leave.objects.filter(
            employee=self.request.user.employee,
            status='pending'
        )
    
    def form_valid(self, form):
        leave = self.get_object()
        leave.status = 'cancelled'
        leave.save()
        
        messages.success(self.request, 'Permiso cancelado exitosamente.')
        return redirect('leave:list')

        """