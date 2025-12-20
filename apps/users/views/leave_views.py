from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.utils import timezone
from datetime import datetime, timedelta

from ..models import UserProfile, Department, Attendance, Leave
from ..forms import (
    LeaveRequestForm, LeaveApprovalForm
)


class LeaveListView(LoginRequiredMixin, ListView):
    """Lista de permisos (para el empleado)"""
    model = Leave
    template_name = 'users/leaves/LeaveList.html'
    context_object_name = 'leaves'
    paginate_by = 20
    
    def get_queryset(self):
        return Leave.objects.filter(
            employee=self.request.user.profile
        ).order_by('-created_at')


class LeaveCreateView(LoginRequiredMixin, CreateView):
    """Solicitar un permiso"""
    model = Leave
    form_class = LeaveRequestForm
    template_name = 'users/leaves/LeaveForm.html'
    success_url = reverse_lazy('leave:list')
    
    def form_valid(self, form):
        form.instance.employee = self.request.user.profile
        messages.success(self.request, 'Solicitud de permiso enviada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Solicitar Permiso'
        context['button_text'] = 'Enviar Solicitud'
        return context


class LeaveDetailView(LoginRequiredMixin, DetailView):
    """Detalle de un permiso"""
    model = Leave
    template_name = 'users/leaves/LeaveDetail.html'
    context_object_name = 'leave'


class LeaveManagementView(LoginRequiredMixin, ListView):
    """Gestión de permisos (para supervisores/RRHH)"""
    model = Leave
    template_name = 'users/leaves/LeaveManagement.html'
    context_object_name = 'leaves'
    paginate_by = 20
    
    def get_queryset(self):
        status = self.request.GET.get('status', 'pending')
        queryset = Leave.objects.select_related('employee', 'employee__user').order_by('-created_at')
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas
        context['stats'] = {
            'pending': Leave.objects.filter(status='pending').count(),
            'approved': Leave.objects.filter(status='approved').count(),
            'rejected': Leave.objects.filter(status='rejected').count()
        }
        
        return context


class LeaveApprovalView(LoginRequiredMixin, UpdateView):
    """Aprobar/Rechazar permiso"""
    model = Leave
    form_class = LeaveApprovalForm
    template_name = 'users/leaves/LeaveApproval.html'
    success_url = reverse_lazy('leave:management')
    
    def form_valid(self, form):
        form.save(user=self.request.user)
        
        leave = self.object
        if leave.status == 'approved':
            messages.success(self.request, f'Permiso aprobado para {leave.employee.get_full_name()}')
        else:
            messages.warning(self.request, f'Permiso rechazado para {leave.employee.get_full_name()}')
        
        return super().form_valid(form)

