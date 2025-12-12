from django.shortcuts import render

# Create your views here.

from django.shortcuts import render
from apps.users.models import Department

from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView

from django.views.generic.edit import UpdateView, DeleteView
from django.urls import reverse_lazy
from apps.forms.users_forms import DepartmentForm

class DepartmentListView(ListView):
    model = Department
    template_name = "users/Departments/DepartmentList.html"
    context_object_name = "departamentos"


class DepartmentDetailView(DetailView):
    model = Department
    template_name = "users/Departments/DepartmentDetail.html"
    context_object_name = "departamento"


class DepartmentCreateView(CreateView):
    model = Department
    form_class = DepartmentForm
    fields = ["name", "color", "código", "descripcion"]
    template_name = "users/Departments/DepartmentCreate.html"


class DepartmentUpdateView(UpdateView):
    model = Department
    form_class = DepartmentForm
    fields = ["name", "color", "código", "descripcion"]
    template_name = "users/Departments/DepartmentUpdate.html"
    context_object_name = "departamento"


class DepartmentDeleteView(DeleteView):
    model = Department
    success_url =reverse_lazy('department:List')
    context_object_name = "departamento"
    template_name = "users/Departments/DepartmentDelete.html"