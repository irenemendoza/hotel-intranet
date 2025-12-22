from django import forms
from django.core.exceptions import ValidationError
from .models import Leave
from django.utils import timezone
from django.contrib.auth.models import User

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