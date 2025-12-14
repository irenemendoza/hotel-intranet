from django import forms
from django.core.exceptions import ValidationError
from apps.users.models import Department
from apps.users.models import ColorChoices

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