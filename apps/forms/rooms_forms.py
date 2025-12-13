from django import forms
from django.utils import timezone
from .models import Room, RoomType, CleaningTask, MaintenanceRequest
from apps.users.models import UserProfile

class RoomTypeForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = ['name', 'code', 'capacity', 'base_price', 'description', 'amenities', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Suite Deluxe'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'text-transform: uppercase;',
                'maxlength': '10',
                'placeholder': 'Ej: SUI-DLX'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10'
            }),
            'base_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del tipo de habitación...'
            }),
            'amenities': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Lista de comodidades: WiFi, TV, Minibar, etc.'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_code(self):
        code = self.cleaned_data.get('code', '').upper()
        if not code:
            raise forms.ValidationError('El código es requerido')
        return code


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['number', 'floor', 'room_type', 'status', 'occupancy', 'notes', 'is_active']
        widgets = {
            'number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 101, 201, 301A'
            }),
            'floor': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '50'
            }),
            'room_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'occupancy': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas adicionales sobre la habitación...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class CleaningTaskForm(forms.ModelForm):
    class Meta:
        model = CleaningTask
        fields = ['room', 'assigned_to', 'cleaning_type', 'priority', 'scheduled_time', 'notes']
        widgets = {
            'room': forms.Select(attrs={
                'class': 'form-control'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-control'
            }),
            'cleaning_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5'
            }),
            'scheduled_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Instrucciones especiales...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo usuarios del departamento de limpieza
        from apps.users.models import Department
        try:
            limpieza_dept = Department.objects.get(code='LIM')
            cleaning_staff = UserProfile.objects.filter(
                department=limpieza_dept,
                is_available=True
            ).select_related('user')
            self.fields['assigned_to'].queryset = User.objects.filter(
                id__in=cleaning_staff.values_list('user_id', flat=True)
            )
            self.fields['assigned_to'].label_from_instance = lambda obj: obj.get_full_name() or obj.username
        except Department.DoesNotExist:
            pass
        
        # Filtrar solo habitaciones sucias o que necesiten limpieza
        self.fields['room'].queryset = Room.objects.filter(
            is_active=True
        ).exclude(status=Room.StatusChoices.CLEAN)


class CleaningTaskUpdateForm(forms.ModelForm):
    """Formulario para que el personal de limpieza actualice el estado"""
    class Meta:
        model = CleaningTask
        fields = ['status', 'notes', 'photos']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas sobre la limpieza realizada...'
            }),
            'photos': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Si se marca como completada, registrar la hora
        if instance.status == CleaningTask.StatusChoices.COMPLETED and not instance.completed_at:
            instance.completed_at = timezone.now()
            if not instance.started_at:
                instance.started_at = timezone.now()
            # Actualizar el estado de la habitación
            instance.room.status = Room.StatusChoices.CLEAN
            instance.room.last_cleaned = timezone.now()
            instance.room.save()
        
        # Si se marca como en progreso, registrar hora de inicio
        elif instance.status == CleaningTask.StatusChoices.IN_PROGRESS and not instance.started_at:
            instance.started_at = timezone.now()
        
        if commit:
            instance.save()
        return instance


class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['room', 'title', 'description', 'priority', 'photos']
        widgets = {
            'room': forms.Select(attrs={
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Aire acondicionado no funciona'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe el problema en detalle...'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'photos': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        if user:
            instance.reported_by = user
        if commit:
            instance.save()
            # Actualizar estado de la habitación
            instance.room.status = Room.StatusChoices.MAINTENANCE
            instance.room.save()
        return instance


class MaintenanceRequestUpdateForm(forms.ModelForm):
    """Formulario para actualizar el estado del mantenimiento"""
    class Meta:
        model = MaintenanceRequest
        fields = ['assigned_to', 'status', 'resolution']
        widgets = {
            'assigned_to': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'resolution': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe cómo se resolvió el problema...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo usuarios del departamento de mantenimiento
        from apps.users.models import Department
        try:
            mant_dept = Department.objects.get(code='MAN')
            maintenance_staff = UserProfile.objects.filter(
                department=mant_dept,
                is_available=True
            ).select_related('user')
            self.fields['assigned_to'].queryset = User.objects.filter(
                id__in=maintenance_staff.values_list('user_id', flat=True)
            )
            self.fields['assigned_to'].label_from_instance = lambda obj: obj.get_full_name() or obj.username
        except Department.DoesNotExist:
            pass
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Actualizar fechas según el estado
        if instance.status == MaintenanceRequest.StatusChoices.ASSIGNED and not instance.assigned_at:
            instance.assigned_at = timezone.now()
        elif instance.status == MaintenanceRequest.StatusChoices.IN_PROGRESS and not instance.started_at:
            instance.started_at = timezone.now()
        elif instance.status == MaintenanceRequest.StatusChoices.COMPLETED and not instance.resolved_at:
            instance.resolved_at = timezone.now()
            # Actualizar estado de la habitación
            instance.room.status = Room.StatusChoices.INSPECTED
            instance.room.save()
        
        if commit:
            instance.save()
        return instance