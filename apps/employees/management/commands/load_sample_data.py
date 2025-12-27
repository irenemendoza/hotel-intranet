# apps/employees/management/commands/load_sample_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from apps.employees.models import Department, Employee
from apps.rooms.models import RoomType, Room
from apps.attendance.models import Attendance
from apps.leave.models import Leave


class Command(BaseCommand):
    help = 'Carga datos de prueba en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Elimina todos los datos antes de cargar los nuevos',
        )

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write(self.style.WARNING('🗑️  Limpiando datos existentes...'))
            self.clean_data()

        self.stdout.write(self.style.SUCCESS('📦 Cargando datos de prueba...'))
        
        # Crear departamentos
        departments = self.create_departments()
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(departments)} departamentos'))
        
        # Crear empleados
        employees = self.create_employees(departments)
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(employees)} empleados'))
        
        # Crear tipos de habitación
        room_types = self.create_room_types()
        self.stdout.write(self.style.SUCCESS(f'✅ Creados {len(room_types)} tipos de habitación'))
        
        # Crear habitaciones
        rooms = self.create_rooms(room_types)
        self.stdout.write(self.style.SUCCESS(f'✅ Creadas {len(rooms)} habitaciones'))
        
        # Crear algunas asistencias
        self.create_sample_attendances(employees)
        self.stdout.write(self.style.SUCCESS('✅ Creadas asistencias de ejemplo'))
        
        # Crear algunas solicitudes de permiso
        self.create_sample_leaves(employees)
        self.stdout.write(self.style.SUCCESS('✅ Creadas solicitudes de permiso'))
        
        self.stdout.write(self.style.SUCCESS('\n✨ ¡Datos de prueba cargados exitosamente!'))
        self.print_credentials()

    def clean_data(self):
        """Elimina todos los datos existentes"""
        Attendance.objects.all().delete()
        Leave.objects.all().delete()
        Room.objects.all().delete()
        RoomType.objects.all().delete()
        Employee.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Department.objects.all().delete()

    def create_departments(self):
        """Crea los departamentos del hotel"""
        departments_data = [
            {'name': 'Dirección', 'code': 'DIR', 'color': '#8B5CF6', 
             'description': 'Dirección general del hotel'},
            {'name': 'Recepción', 'code': 'REC', 'color': '#3B82F6', 
             'description': 'Atención al cliente y check-in/out'},
            {'name': 'Limpieza', 'code': 'LIM', 'color': '#10B981', 
             'description': 'Limpieza y mantenimiento de habitaciones'},
            {'name': 'Mantenimiento', 'code': 'MAN', 'color': '#F59E0B', 
             'description': 'Mantenimiento técnico e instalaciones'},
            {'name': 'Recursos Humanos', 'code': 'RRHH', 'color': '#EC4899', 
             'description': 'Gestión de personal'},
        ]
        
        departments = {}
        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults=dept_data
            )
            departments[dept_data['code']] = dept
        
        return departments

    def create_employees(self, departments):
        """Crea un empleado por cada rol"""
        employees_data = [
            # Dirección
            {
                'username': 'director',
                'password': 'director123',
                'first_name': 'Carlos',
                'last_name': 'Martínez',
                'email': 'director@hotel.com',
                'department': departments['DIR'],
                'role': 'director',
                'phone': '+34 600 111 111',
                'employee_number': 'EMP001',
            },
            # Recepción
            {
                'username': 'jefe_recepcion',
                'password': 'jefe123',
                'first_name': 'Ana',
                'last_name': 'García',
                'email': 'jefe.recepcion@hotel.com',
                'department': departments['REC'],
                'role': 'jefe_recepcion',
                'phone': '+34 600 222 222',
                'employee_number': 'EMP002',
            },
            {
                'username': 'recepcionista',
                'password': 'recepcion123',
                'first_name': 'María',
                'last_name': 'López',
                'email': 'recepcion@hotel.com',
                'department': departments['REC'],
                'role': 'recepcionista',
                'phone': '+34 600 333 333',
                'employee_number': 'EMP003',
            },
            # Limpieza
            {
                'username': 'jefe_limpieza',
                'password': 'limpieza123',
                'first_name': 'Pedro',
                'last_name': 'Sánchez',
                'email': 'jefe.limpieza@hotel.com',
                'department': departments['LIM'],
                'role': 'jefe_limpieza',
                'phone': '+34 600 444 444',
                'employee_number': 'EMP004',
            },
            {
                'username': 'camarera1',
                'password': 'camarera123',
                'first_name': 'Laura',
                'last_name': 'Fernández',
                'email': 'camarera1@hotel.com',
                'department': departments['LIM'],
                'role': 'camarero_piso',
                'phone': '+34 600 555 555',
                'employee_number': 'EMP005',
            },
            {
                'username': 'camarera2',
                'password': 'camarera123',
                'first_name': 'Carmen',
                'last_name': 'Ruiz',
                'email': 'camarera2@hotel.com',
                'department': departments['LIM'],
                'role': 'camarero_piso',
                'phone': '+34 600 666 666',
                'employee_number': 'EMP006',
            },
            # Mantenimiento
            {
                'username': 'jefe_mantenimiento',
                'password': 'manten123',
                'first_name': 'José',
                'last_name': 'Morales',
                'email': 'jefe.mantenimiento@hotel.com',
                'department': departments['MAN'],
                'role': 'jefe_mantenimiento',
                'phone': '+34 600 777 777',
                'employee_number': 'EMP007',
            },
            {
                'username': 'tecnico1',
                'password': 'tecnico123',
                'first_name': 'Miguel',
                'last_name': 'Torres',
                'email': 'tecnico@hotel.com',
                'department': departments['MAN'],
                'role': 'mantenimiento',
                'phone': '+34 600 888 888',
                'employee_number': 'EMP008',
            },
            # RRHH
            {
                'username': 'rrhh',
                'password': 'rrhh123',
                'first_name': 'Isabel',
                'last_name': 'Ramírez',
                'email': 'rrhh@hotel.com',
                'department': departments['RRHH'],
                'role': 'rrhh',
                'phone': '+34 600 999 999',
                'employee_number': 'EMP009',
            },
        ]
        
        employees = []
        for emp_data in employees_data:
            # Crear usuario
            user, created = User.objects.get_or_create(
                username=emp_data['username'],
                defaults={
                    'first_name': emp_data['first_name'],
                    'last_name': emp_data['last_name'],
                    'email': emp_data['email'],
                    'is_staff': emp_data['role'] in ['director', 'rrhh'],
                }
            )
            if created:
                user.set_password(emp_data['password'])
                user.save()
            
            # Crear empleado
            employee, created = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'department': emp_data['department'],
                    'role': emp_data['role'],
                    'phone': emp_data['phone'],
                    'employee_number': emp_data['employee_number'],
                    'hire_date': timezone.now().date() - timedelta(days=180),
                    'is_available': True,
                }
            )
            employees.append(employee)
        
        return employees

    def create_room_types(self):
        """Crea tipos de habitación"""
        room_types_data = [
            {
                'name': 'Individual',
                'code': 'IND',
                'capacity': 1,
                'description': 'Habitación para una persona',
                'amenities': 'Cama individual, TV, WiFi, Escritorio',
            },
            {
                'name': 'Doble',
                'code': 'DBL',
                'capacity': 2,
                'description': 'Habitación para dos personas',
                'amenities': 'Cama doble o dos camas, TV, WiFi, Minibar',
            },
            {
                'name': 'Suite',
                'code': 'SUI',
                'capacity': 4,
                'description': 'Suite de lujo',
                'amenities': 'Cama king, Sala de estar, TV, WiFi, Minibar, Jacuzzi',
            },
            {
                'name': 'Familiar',
                'code': 'FAM',
                'capacity': 4,
                'description': 'Habitación familiar amplia',
                'amenities': 'Cama doble + litera, TV, WiFi, Zona de juegos',
            },
        ]
        
        room_types = {}
        for rt_data in room_types_data:
            rt, created = RoomType.objects.get_or_create(
                code=rt_data['code'],
                defaults=rt_data
            )
            room_types[rt_data['code']] = rt
        
        return room_types

    def create_rooms(self, room_types):
        """Crea habitaciones distribuidas en 3 pisos"""
        rooms = []
        room_distribution = {
            1: [  # Piso 1
                ('101', 'IND'), ('102', 'IND'), ('103', 'DBL'), 
                ('104', 'DBL'), ('105', 'DBL'),
            ],
            2: [  # Piso 2
                ('201', 'DBL'), ('202', 'DBL'), ('203', 'DBL'),
                ('204', 'FAM'), ('205', 'FAM'),
            ],
            3: [  # Piso 3
                ('301', 'SUI'), ('302', 'SUI'), ('303', 'DBL'),
                ('304', 'DBL'), ('305', 'FAM'),
            ],
        }
        
        statuses = ['clean', 'dirty', 'clean', 'clean', 'dirty']
        occupancies = ['vacant', 'occupied', 'vacant', 'vacant', 'occupied']
        
        idx = 0
        for floor, floor_rooms in room_distribution.items():
            for number, type_code in floor_rooms:
                room, created = Room.objects.get_or_create(
                    number=number,
                    defaults={
                        'floor': floor,
                        'room_type': room_types[type_code],
                        'status': statuses[idx % len(statuses)],
                        'occupancy': occupancies[idx % len(occupancies)],
                        'is_active': True,
                    }
                )
                rooms.append(room)
                idx += 1
        
        return rooms

    def create_sample_attendances(self, employees):
        """Crea registros de asistencia de ejemplo"""
        today = timezone.now().date()
        
        # Asistencias de hoy (algunos fichados, otros no)
        for i, employee in enumerate(employees[:6]):  # Solo 6 primeros
            check_in_time = timezone.now().replace(
                hour=8 + (i % 2),  # 8:00 o 9:00
                minute=0 if i % 2 == 0 else 15,
                second=0,
                microsecond=0
            )
            
            Attendance.objects.get_or_create(
                employee=employee,
                check_in__date=today,
                defaults={
                    'check_in': check_in_time,
                    'status': 'present' if i % 2 == 0 else 'late',
                }
            )
        
        # Asistencias de días anteriores (completas)
        for days_ago in range(1, 6):
            date = today - timedelta(days=days_ago)
            for employee in employees:
                check_in = timezone.datetime.combine(
                    date, 
                    timezone.datetime.min.time()
                ).replace(hour=8, minute=30, tzinfo=timezone.get_current_timezone())
                
                check_out = check_in + timedelta(hours=8)
                
                Attendance.objects.get_or_create(
                    employee=employee,
                    check_in__date=date,
                    defaults={
                        'check_in': check_in,
                        'check_out': check_out,
                        'status': 'present',
                    }
                )

    def create_sample_leaves(self, employees):
        """Crea solicitudes de permiso de ejemplo"""
        today = timezone.now().date()
        
        # Permiso pendiente
        Leave.objects.get_or_create(
            employee=employees[4],  # Camarera 1
            start_date=today + timedelta(days=7),
            defaults={
                'end_date': today + timedelta(days=9),
                'leave_type': 'vacation',
                'reason': 'Vacaciones familiares',
                'status': 'pending',
            }
        )
        
        # Permiso aprobado
        Leave.objects.get_or_create(
            employee=employees[2],  # Recepcionista
            start_date=today - timedelta(days=3),
            defaults={
                'end_date': today - timedelta(days=1),
                'leave_type': 'sick',
                'reason': 'Gripe',
                'status': 'approved',
                'approved_by': employees[0].user,  # Director
                'approved_at': timezone.now() - timedelta(days=4),
            }
        )

    def print_credentials(self):
        """Imprime las credenciales de los usuarios creados"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📋 CREDENCIALES DE ACCESO'))
        self.stdout.write('='*60 + '\n')
        
        credentials = [
            ('Director', 'director', 'director123'),
            ('Jefe Recepción', 'jefe_recepcion', 'jefe123'),
            ('Recepcionista', 'recepcionista', 'recepcion123'),
            ('Jefe Limpieza', 'jefe_limpieza', 'limpieza123'),
            ('Camarera 1', 'camarera1', 'camarera123'),
            ('Camarera 2', 'camarera2', 'camarera123'),
            ('Jefe Mantenimiento', 'jefe_mantenimiento', 'manten123'),
            ('Técnico', 'tecnico1', 'tecnico123'),
            ('RRHH', 'rrhh', 'rrhh123'),
        ]
        
        for role, username, password in credentials:
            self.stdout.write(
                f'  {role:20} | Usuario: {username:20} | Contraseña: {password}'
            )
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('💡 Puedes iniciar sesión con cualquiera de estos usuarios')
        self.stdout.write('='*60 + '\n')