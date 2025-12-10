from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.users.models import Department, UserProfile
from apps.rooms.models import RoomType, Room

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **kwargs):
        # Crear departamentos
        departments_data = [
            {'name': 'Dirección', 'code': 'DIR'},
            {'name': 'Recepción', 'code': 'REC'},
            {'name': 'Limpieza', 'code': 'LIM'},
            {'name': 'Mantenimiento', 'code': 'MAN'},
            {'name': 'Restaurante', 'code': 'RES'},
        ]
        
        for dept_data in departments_data:
            Department.objects.get_or_create(**dept_data)
        
        self.stdout.write(self.style.SUCCESS('Departamentos creados'))
        
        # Crear tipos de habitación
        room_types_data = [
            {'name': 'Individual', 'code': 'IND', 'capacity': 1, 'base_price': 50.00},
            {'name': 'Doble', 'code': 'DBL', 'capacity': 2, 'base_price': 80.00},
            {'name': 'Suite', 'code': 'SUI', 'capacity': 4, 'base_price': 150.00},
        ]
        
        for rt_data in room_types_data:
            RoomType.objects.get_or_create(**rt_data)
        
        self.stdout.write(self.style.SUCCESS('Tipos de habitación creados'))
        
        # Crear algunas habitaciones
        room_types = list(RoomType.objects.all())
        for floor in range(1, 4):
            for num in range(1, 6):
                room_number = f"{floor}0{num}"
                Room.objects.get_or_create(
                    number=room_number,
                    defaults={
                        'floor': floor,
                        'room_type': room_types[(floor + num) % len(room_types)]
                    }
                )
        
        self.stdout.write(self.style.SUCCESS('Habitaciones creadas'))
        self.stdout.write(self.style.SUCCESS('✅ Base de datos poblada exitosamente'))