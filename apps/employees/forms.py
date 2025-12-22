from django import forms
from django.core.exceptions import ValidationError
from .models import Department, Employee
from django.utils import timezone
from django.contrib.auth.models import User

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'color', 'code', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Recepción'
            }),
            'color': forms.Select(attrs={
                'class': 'form-control'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'text-transform: uppercase;',
                'maxlength': '3',
                'placeholder': 'Ej: REC'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción del departamento...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'Nombre del Departamento',
            'color': 'Color Identificativo',
            'code': 'Código',
            'description': 'Descripción',
            'is_active': 'Departamento Activo'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar colores ya utilizados (excepto el actual si estamos editando)
        used_colors = Department.objects.exclude(
            pk=self.instance.pk if self.instance.pk else None
        ).values_list('color', flat=True)
        
        available_choices = [
            choice for choice in ColorChoices.choices 
            if choice[0] not in used_colors
        ]
        
        if available_choices:
            self.fields['color'].choices = available_choices
        else:
            self.fields['color'].help_text = 'No hay colores disponibles'
    
    def clean_code(self):
        code = self.cleaned_data.get('code', '').upper()
        
        if len(code) != 3:
            raise ValidationError('El código debe tener exactamente 3 caracteres')
        
        if not code.isalpha():
            raise ValidationError('El código solo puede contener letras')
        
        return code


class EmployeeForm(forms.ModelForm):
    # Campos del User
    first_name = forms.CharField(
        label='Nombre',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='Apellidos',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Employee
        fields = [
            'department', 'role', 'phone', 'employee_number',
            'hire_date', 'avatar', 'bio', 'is_available'
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Recepcionista, Camarera de pisos...'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+34 600 000 000'
            }),
            'employee_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: EMP001'
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Información adicional sobre el empleado...'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prellenar campos del User si existe
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Actualizar campos del User
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            profile.save()
        
        return profile


