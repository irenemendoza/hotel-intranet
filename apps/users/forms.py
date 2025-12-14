from django import forms
from django.core.exceptions import ValidationError
from .models import Department, ColorChoices, UserProfile, Attendance, Leave
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


class UserProfileForm(forms.ModelForm):
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
        model = UserProfile
        fields = [
            'department', 'position', 'phone', 'employee_number',
            'hire_date', 'avatar', 'bio', 'is_available'
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={
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


class AttendanceCheckInForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['notes', 'check_in_location']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notas opcionales...'
            }),
            'check_in_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ubicación (opcional)'
            })
        }


class AttendanceCheckOutForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['notes', 'check_out_location']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Resumen del día...'
            }),
            'check_out_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ubicación (opcional)'
            })
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.check_out = timezone.now()
        
        if commit:
            instance.save()
        
        return instance


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = ['leave_type', 'start_date', 'end_date', 'reason', 'attachment']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Explica el motivo de tu solicitud...'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError('La fecha de fin no puede ser anterior a la fecha de inicio')
            
            if start_date < timezone.now().date():
                raise ValidationError('No puedes solicitar permisos para fechas pasadas')
        
        return cleaned_data


class LeaveApprovalForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = ['status', 'rejection_reason']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'rejection_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Motivo del rechazo (si aplica)...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar opciones aprobado/rechazado
        self.fields['status'].choices = [
            ('approved', 'Aprobar'),
            ('rejected', 'Rechazar'),
        ]
    
    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        
        if user:
            instance.approved_by = user
            instance.approved_at = timezone.now()
        
        if commit:
            instance.save()
        
        return instance