from django import forms
from django.core.exceptions import ValidationError
from apps.users.models import Department

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'color', 'code', 'description', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'style': 'text-transform: uppercase;',
                'maxlength': '3',
                'placeholder': 'Ej: ADM'
            })
        }
    
    def clean_code(self):
        code = self.cleaned_data.get('code', '').upper()
        
        # Validar longitud
        if len(code) != 3:
            raise ValidationError('El código debe tener exactamente 3 caracteres')
        
        # Validar que solo contenga letras
        if not code.isalpha():
            raise ValidationError('El código solo puede contener letras')
        
        return code