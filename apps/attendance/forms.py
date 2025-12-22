from django import forms
from django.core.exceptions import ValidationError
from .models import Attendance
from django.utils import timezone
from django.contrib.auth.models import User

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


