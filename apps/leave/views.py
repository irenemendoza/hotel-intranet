from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView
from .models import Leave

from django.urls import reverse_lazy
from .forms import LeaveRequestForm

class LeaveListView(LoginRequiredMixin, ListView):
    """Lista de permisos (para el empleado)"""
    model = Leave
    template_name = 'leaves/LeaveList.html'
    context_object_name = 'leaves'
    paginate_by = 20
    
    def get_queryset(self):
        return Leave.objects.filter(
            employee=self.request.user.employee
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas personales
        employee = self.request.user.employee
        
        context['available_days'] = 22  # Calcular según el caso
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
    """Solicitar un permiso"""
    model = Leave
    form_class = LeaveRequestForm
    template_name = 'eaves/LeaveRequestForm.html'
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