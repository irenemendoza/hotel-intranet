from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from apps.users.models import Department, UserProfile

from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView

from django.views.generic.edit import UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.forms.users_forms import DepartmentForm

class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = "users/Departments/DepartmentList.html"
    context_object_name = "departments"

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrar por activos si se requiere
        show_inactive = self.request.GET.get('show_inactive', False)
        if not show_inactive:
            queryset = queryset.filter(is_active=True)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_departments'] = Department.objects.count()
        context['activos'] = Department.objects.filter(is_active=True).count()
        return context


class DepartmentDetailView(LoginRequiredMixin, DetailView):
    model = Department
    template_name = "users/Departments/DepartmentDetail.html"
    context_object_name = "department"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        department = self.object

        empleados = UserProfile.objects.filter(department=department)

        context["empleados"] = empleados
        context["total_empleados"] = empleados.count()

        # Filtrar empleados disponibles y no disponibles
        context["empleados_disponibles"] = empleados.filter(is_available=True).count()
        context["empleados_no_disponibles"] = empleados.filter(is_available=False).count()

        return context


class DepartmentCreateView(CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = "users/Departments/DepartmentForm.html"
    success_url = reverse_lazy('department:list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Departamento "{form.instance.name}" creado exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Departamento'
        context['button_text'] = 'Crear'
        return context

class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = "users/Departments/DepartmentForm.html"
    context_object_name = "department"
    success_url = reverse_lazy('department:list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Departamento "{form.instance.name}" actualizado exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Departamento'
        context['button_text'] = 'Actualizar'
        return context


class DepartmentDeleteView(DeleteView):
    model = Department
    success_url =reverse_lazy('department:List')
    context_object_name = "department"
    template_name = "users/Departments/DepartmentDelete.html"

    def delete(self, request, *args, **kwargs):
        department = self.get_object()
        messages.success(request, f'Departamento "{department.name}" eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)