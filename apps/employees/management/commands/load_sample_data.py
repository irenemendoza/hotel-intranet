# apps/employees/management/commands/load_sample_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import random

from apps.employees.models import Department, Employee
from apps.attendance.models import Attendance
from apps.leave.models import Leave
from apps.rooms.models import RoomType, Room, Reservation, CleaningTask, MaintenanceTask


class Command(BaseCommand):
    help = 'Carga datos de prueba en la base de datos'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando carga de datos de prueba...'))
        
        # Limpiar datos existentes (opcional)
        self.stdout.write('Limpiando datos existentes...')
        self.clear_data()
        
        # Crear grupos
        self.stdout.write('Creando grupos...')
        self.create_groups()
        
        # Crear departamentos
        self.stdout.write('Creando departamentos...')
        departments = self.create_departments()
        
        # Crear usuarios y empleados
        self.stdout.write('Creando usuarios y empleados...')
        employees = self.create_employees(departments)
        
        # Crear tipos de habitaciones
        self.stdout.write('Creando tipos de habitaciones...')
        room_types = self.create_room_types()
        
        # Crear habitaciones
        self.stdout.write('Creando habitaciones...')
        rooms = self.create_rooms(room_types)
        
        # Crear reservas
        self.stdout.write('Creando reservas...')
        reservations = self.create_reservations(rooms, employees)
        
        # Crear registros de asistencia
        self.stdout.write('Creando registros de asistencia...')
        self.create_attendances(employees)
        
        # Crear solicitudes de permisos
        self.stdout.write('Creando solicitudes de permisos...')
        self.create_leaves(employees)
        
        # Crear tareas de limpieza
        self.stdout.write('Creando tareas de limpieza...')
        self.create_cleaning_tasks(rooms, employees)
        
        # Crear tareas de mantenimiento
        self.stdout.write('Creando tareas de mantenimiento...')
        self.create_maintenance_tasks(rooms, employees)
        
        self.stdout.write(self.style.SUCCESS('✓ Datos de prueba cargados exitosamente!'))
        self.print_summary(employees, rooms, reservations)

    def clear_data(self):
        """Limpia datos existentes (excepto superusuarios)"""
        MaintenanceTask.objects.all().delete()
        CleaningTask.objects.all().delete()
        Reservation.objects.all().delete()
        Leave.objects.all().delete()
        Attendance.objects.all().delete()
        Room.objects.all().delete()
        RoomType.objects.all().delete()
        Employee.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Department.objects.all().delete()

    def create_groups(self):
        """Crea los grupos de usuarios"""
        groups = [
            'Dirección', 'Recepción', 'Limpieza', 
            'Mantenimiento', 'RRHH', 'Supervisores'
        ]
        for group_name in groups:
            Group.objects.get_or_create(name=group_name)

    def create_departments(self):
        """Crea los departamentos del hotel"""
        departments_data = [
            {'name': 'Dirección', 'code': 'DIR', 'color': '#3B82F6'},
            {'name': 'Recepción', 'code': 'REC', 'color': '#10B981'},
            {'name': 'Limpieza', 'code': 'LIM', 'color': '#F59E0B'},
            {'name': 'Mantenimiento', 'code': 'MAN', 'color': '#EF4444'},
            {'name': 'Recursos Humanos', 'code': 'RRH', 'color': '#8B5CF6'},
        ]
        
        departments = {}
        for dept_data in departments_data:
            dept = Department.objects.create(
                name=dept_data['name'],
                code=dept_data['code'],
                color=dept_data['color'],
                description=f'Departamento de {dept_data["name"]}',
                is_active=True
            )
            departments[dept_data['code']] = dept
        
        return departments

    def create_employees(self, departments):
        """Crea usuarios y sus perfiles de empleado"""
        employees_data = [
            # Dirección
            {
                'username': 'director',
                'password': 'director123',
                'first_name': 'Carlos',
                'last_name': 'Rodríguez',
                'email': 'carlos.rodriguez@hotel.com',
                'department': departments['DIR'],
                'role': 'director',
                'phone': '+34 600 111 111',
                'employee_number': 'EMP001'
            },
            # Recepción
            {
                'username': 'jefe.recepcion',
                'password': 'recepcion123',
                'first_name': 'María',
                'last_name': 'García',
                'email': 'maria.garcia@hotel.com',
                'department': departments['REC'],
                'role': 'jefe_recepcion',
                'phone': '+34 600 222 222',
                'employee_number': 'EMP002'
            },
            {
                'username': 'ana.recepcion',
                'password': 'recepcion123',
                'first_name': 'Ana',
                'last_name': 'Martínez',
                'email': 'ana.martinez@hotel.com',
                'department': departments['REC'],
                'role': 'recepcionista',
                'phone': '+34 600 333 333',
                'employee_number': 'EMP003'
            },
            {
                'username': 'pedro.recepcion',
                'password': 'recepcion123',
                'first_name': 'Pedro',
                'last_name': 'López',
                'email': 'pedro.lopez@hotel.com',
                'department': departments['REC'],
                'role': 'recepcionista',
                'phone': '+34 600 444 444',
                'employee_number': 'EMP004'
            },
            # Limpieza
            {
                'username': 'jefe.limpieza',
                'password': 'limpieza123',
                'first_name': 'Laura',
                'last_name': 'Fernández',
                'email': 'laura.fernandez@hotel.com',
                'department': departments['LIM'],
                'role': 'jefe_limpieza',
                'phone': '+34 600 555 555',
                'employee_number': 'EMP005'
            },
            {
                'username': 'carmen.limpieza',
                'password': 'limpieza123',
                'first_name': 'Carmen',
                'last_name': 'Ruiz',
                'email': 'carmen.ruiz@hotel.com',
                'department': departments['LIM'],
                'role': 'camarero_piso',
                'phone': '+34 600 666 666',
                'employee_number': 'EMP006'
            },
            {
                'username': 'isabel.limpieza',
                'password': 'limpieza123',
                'first_name': 'Isabel',
                'last_name': 'Sánchez',
                'email': 'isabel.sanchez@hotel.com',
                'department': departments['LIM'],
                'role': 'camarero_piso',
                'phone': '+34 600 777 777',
                'employee_number': 'EMP007'
            },
            {
                'username': 'rosa.limpieza',
                'password': 'limpieza123',
                'first_name': 'Rosa',
                'last_name': 'Moreno',
                'email': 'rosa.moreno@hotel.com',
                'department': departments['LIM'],
                'role': 'camarero_piso',
                'phone': '+34 600 888 888',
                'employee_number': 'EMP008'
            },
            # Mantenimiento
            {
                'username': 'jefe.mantenimiento',
                'password': 'mantenimiento123',
                'first_name': 'Miguel',
                'last_name': 'Torres',
                'email': 'miguel.torres@hotel.com',
                'department': departments['MAN'],
                'role': 'jefe_mantenimiento',
                'phone': '+34 600 999 999',
                'employee_number': 'EMP009'
            },
            {
                'username': 'juan.mantenimiento',
                'password': 'mantenimiento123',
                'first_name': 'Juan',
                'last_name': 'Díaz',
                'email': 'juan.diaz@hotel.com',
                'department': departments['MAN'],
                'role': 'mantenimiento',
                'phone': '+34 601 111 111',
                'employee_number': 'EMP010'
            },
            {
                'username': 'antonio.mantenimiento',
                'password': 'mantenimiento123',
                'first_name': 'Antonio',
                'last_name': 'Jiménez',
                'email': 'antonio.jimenez@hotel.com',
                'department': departments['MAN'],
                'role': 'mantenimiento',
                'phone': '+34 601 222 222',
                'employee_number': 'EMP011'
            },
            # RRHH
            {
                'username': 'rrhh',
                'password': 'rrhh123',
                'first_name': 'Elena',
                'last_name': 'Vargas',
                'email': 'elena.vargas@hotel.com',
                'department': departments['RRH'],
                'role': 'rrhh',
                'phone': '+34 601 333 333',
                'employee_number': 'EMP012'
            },
        ]
        
        employees = []
        for emp_data in employees_data:
            # Crear usuario
            user = User.objects.create_user(
                username=emp_data['username'],
                password=emp_data['password'],
                first_name=emp_data['first_name'],
                last_name=emp_data['last_name'],
                email=emp_data['email']
            )
            
            # Actualizar o crear empleado
            employee, created = Employee.objects.update_or_create(
                user=user,
                defaults={
                    'department': emp_data['department'],
                    'role': emp_data['role'],
                    'phone': emp_data['phone'],
                    'employee_number': emp_data['employee_number'],
                    'hire_date': timezone.now().date() - timedelta(days=random.randint(30, 365)),
                    'is_available': True,
                }
            )
            
            employees.append(employee)
            self.stdout.write(f'  ✓ {emp_data["first_name"]} {emp_data["last_name"]} - {emp_data["role"]}')
        
        return employees

    def create_room_types(self):
        """Crea los tipos de habitaciones"""
        room_types_data = [
            {
                'name': 'Individual',
                'code': 'IND',
                'capacity': 1,
                'description': 'Habitación individual con cama sencilla',
                'amenities': 'WiFi, TV, Minibar, Baño privado',
            },
            {
                'name': 'Doble',
                'code': 'DBL',
                'capacity': 2,
                'description': 'Habitación doble con cama matrimonial',
                'amenities': 'WiFi, TV, Minibar, Baño privado, Balcón',
            },
            {
                'name': 'Twin',
                'code': 'TWN',
                'capacity': 2,
                'description': 'Habitación con dos camas individuales',
                'amenities': 'WiFi, TV, Minibar, Baño privado',
            },
            {
                'name': 'Suite',
                'code': 'SUI',
                'capacity': 4,
                'description': 'Suite con sala de estar y habitación separadas',
                'amenities': 'WiFi, TV, Minibar, Baño privado, Jacuzzi, Vista al mar',
            },
            {
                'name': 'Suite Deluxe',
                'code': 'SUI-DLX',
                'capacity': 4,
                'description': 'Suite de lujo con todas las comodidades',
                'amenities': 'WiFi, TV, Minibar, 2 Baños, Jacuzzi, Vista al mar, Terraza privada',
            },
        ]
        
        room_types = []
        for rt_data in room_types_data:
            room_type = RoomType.objects.create(**rt_data)
            room_types.append(room_type)
        
        return room_types

    def create_rooms(self, room_types):
        """Crea las habitaciones del hotel"""
        rooms = []
        
        # Distribución por piso
        floors_config = {
            1: {'start': 101, 'count': 10, 'types': [0, 0, 1, 1, 1, 2, 2, 2, 1, 1]},
            2: {'start': 201, 'count': 10, 'types': [1, 1, 1, 2, 2, 2, 1, 1, 1, 3]},
            3: {'start': 301, 'count': 8, 'types': [1, 2, 2, 3, 3, 4, 1, 2]},
            4: {'start': 401, 'count': 6, 'types': [3, 3, 4, 4, 3, 4]},
        }
        
        statuses = [
            Room.StatusChoices.CLEAN,
            Room.StatusChoices.DIRTY,
            Room.StatusChoices.CLEAN,
            Room.StatusChoices.CLEAN,
        ]
        
        occupancies = [
            Room.OccupancyChoices.VACANT,
            Room.OccupancyChoices.OCCUPIED,
            Room.OccupancyChoices.VACANT,
            Room.OccupancyChoices.RESERVED,
        ]
        
        for floor, config in floors_config.items():
            for i in range(config['count']):
                room_number = config['start'] + i
                type_idx = config['types'][i]
                
                room = Room.objects.create(
                    number=str(room_number),
                    floor=floor,
                    room_type=room_types[type_idx],
                    status=random.choice(statuses),
                    occupancy=random.choice(occupancies),
                    is_active=True,
                    notes=f'Habitación {room_number}'
                )
                
                # Algunas habitaciones con última limpieza
                if random.random() > 0.3:
                    room.last_cleaned = timezone.now() - timedelta(hours=random.randint(1, 48))
                    room.save()
                
                rooms.append(room)
        
        return rooms

    def create_reservations(self, rooms, employees):
        """Crea reservas de ejemplo"""
        reservations = []
        reception_staff = [e for e in employees if e.role == 'recepcionista']
        
        # Datos de huéspedes ficticios
        guests = [
            {'first_name': 'Juan', 'last_name': 'Pérez', 'email': 'juan.perez@email.com', 'phone': '+34 600 100 100', 'dni': '12345678A'},
            {'first_name': 'María', 'last_name': 'González', 'email': 'maria.gonzalez@email.com', 'phone': '+34 600 200 200', 'dni': '23456789B'},
            {'first_name': 'David', 'last_name': 'Martín', 'email': 'david.martin@email.com', 'phone': '+34 600 300 300', 'dni': '34567890C'},
            {'first_name': 'Laura', 'last_name': 'Sánchez', 'email': 'laura.sanchez@email.com', 'phone': '+34 600 400 400', 'dni': '45678901D'},
            {'first_name': 'Carlos', 'last_name': 'López', 'email': 'carlos.lopez@email.com', 'phone': '+34 600 500 500', 'dni': '56789012E'},
        ]
        
        today = timezone.now().date()
        
        # Crear algunas reservas pasadas, actuales y futuras
        for i in range(15):
            guest = random.choice(guests)
            room = random.choice(rooms)
            
            # Determinar fechas según el tipo de reserva
            if i < 5:  # Reservas pasadas (checked out)
                check_in_date = today - timedelta(days=random.randint(5, 30))
                check_out_date = check_in_date + timedelta(days=random.randint(1, 7))
                status = Reservation.StatusChoices.CHECKED_OUT
                actual_check_in = timezone.make_aware(datetime.combine(check_in_date, datetime.min.time()))
                actual_check_out = timezone.make_aware(datetime.combine(check_out_date, datetime.min.time()))
            elif i < 8:  # Reservas actuales (checked in)
                check_in_date = today - timedelta(days=random.randint(0, 3))
                check_out_date = today + timedelta(days=random.randint(1, 5))
                status = Reservation.StatusChoices.CHECKED_IN
                actual_check_in = timezone.make_aware(datetime.combine(check_in_date, datetime.min.time()))
                actual_check_out = None
            else:  # Reservas futuras
                check_in_date = today + timedelta(days=random.randint(1, 30))
                check_out_date = check_in_date + timedelta(days=random.randint(1, 7))
                status = random.choice([
                    Reservation.StatusChoices.PENDING,
                    Reservation.StatusChoices.CONFIRMED
                ])
                actual_check_in = None
                actual_check_out = None
            
            nights = (check_out_date - check_in_date).days
            room_rate = Decimal(str(random.randint(80, 200)))
            total_amount = room_rate * nights
            
            reservation = Reservation.objects.create(
                room=room,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                actual_check_in=actual_check_in,
                actual_check_out=actual_check_out,
                guest_first_name=guest['first_name'],
                guest_last_name=guest['last_name'],
                guest_email=guest['email'],
                guest_phone=guest['phone'],
                guest_dni=guest['dni'],
                guest_nationality='España',
                adults=random.randint(1, 3),
                children=random.randint(0, 2),
                status=status,
                room_rate=room_rate,
                total_amount=total_amount,
                paid_amount=total_amount if status == Reservation.StatusChoices.CHECKED_OUT else Decimal('0'),
                payment_status=Reservation.PaymentStatusChoices.PAID if status == Reservation.StatusChoices.CHECKED_OUT else Reservation.PaymentStatusChoices.UNPAID,
                created_by=reception_staff[0].user if reception_staff else None,
                checked_in_by=reception_staff[0] if status in [Reservation.StatusChoices.CHECKED_IN, Reservation.StatusChoices.CHECKED_OUT] and reception_staff else None,
                checked_out_by=reception_staff[0] if status == Reservation.StatusChoices.CHECKED_OUT and reception_staff else None,
            )
            
            reservations.append(reservation)
        
        return reservations

    def create_attendances(self, employees):
        """Crea registros de asistencia"""
        today = timezone.now().date()
        
        # Crear asistencia de los últimos 30 días
        for days_ago in range(30):
            date = today - timedelta(days=days_ago)
            
            for employee in employees:
                # 90% de probabilidad de asistencia
                if random.random() < 0.9:
                    # Hora de entrada entre 8:00 y 9:30
                    check_in_hour = random.randint(8, 9)
                    check_in_minute = random.randint(0, 59) if check_in_hour == 8 else random.randint(0, 30)
                    check_in = timezone.make_aware(
                        datetime.combine(date, datetime.min.time().replace(hour=check_in_hour, minute=check_in_minute))
                    )
                    
                    # Si no es hoy, crear con salida
                    if days_ago > 0:
                        # Hora de salida entre 17:00 y 19:00
                        check_out_hour = random.randint(17, 18)
                        check_out_minute = random.randint(0, 59)
                        check_out = timezone.make_aware(
                            datetime.combine(date, datetime.min.time().replace(hour=check_out_hour, minute=check_out_minute))
                        )
                    else:
                        # Hoy: 70% con salida, 30% sin salida (aún trabajando)
                        if random.random() < 0.7:
                            check_out_hour = random.randint(17, 18)
                            check_out_minute = random.randint(0, 59)
                            check_out = timezone.make_aware(
                                datetime.combine(date, datetime.min.time().replace(hour=check_out_hour, minute=check_out_minute))
                            )
                        else:
                            check_out = None
                    
                    # Determinar estado
                    status = 'late' if check_in_hour >= 9 else 'present'
                    
                    Attendance.objects.create(
                        employee=employee,
                        check_in=check_in,
                        check_out=check_out,
                        status=status,
                        notes=f'Asistencia del {date.strftime("%d/%m/%Y")}'
                    )

    def create_leaves(self, employees):
        """Crea solicitudes de permisos"""
        today = timezone.now().date()
        leave_types = ['vacation', 'sick', 'personal', 'other']
        statuses = ['pending', 'approved', 'rejected']
        supervisors = [e for e in employees if e.is_supervisor()]
        
        for i in range(20):
            employee = random.choice([e for e in employees if not e.is_supervisor()])
            leave_type = random.choice(leave_types)
            
            # Fechas
            start_offset = random.randint(-30, 60)
            start_date = today + timedelta(days=start_offset)
            end_date = start_date + timedelta(days=random.randint(1, 10))
            
            # Estado
            if start_offset < 0:  # Pasado
                status = random.choice(['approved', 'rejected'])
            else:  # Futuro
                status = random.choice(statuses)
            
            leave = Leave.objects.create(
                employee=employee,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                reason=f'Solicitud de {leave_type} del empleado {employee.get_full_name()}',
                status=status,
                approved_by=random.choice(supervisors).user if status in ['approved', 'rejected'] and supervisors else None,
                approved_at=timezone.now() if status in ['approved', 'rejected'] else None,
                rejection_reason='No disponibilidad de personal' if status == 'rejected' else ''
            )

    def create_cleaning_tasks(self, rooms, employees):
        """Crea tareas de limpieza"""
        cleaning_staff = [e for e in employees if e.role == 'camarero_piso']
        
        # Crear tareas para habitaciones sucias
        dirty_rooms = [r for r in rooms if r.status == Room.StatusChoices.DIRTY]
        
        for room in dirty_rooms[:15]:  # Primeras 15 habitaciones sucias
            assigned = random.choice(cleaning_staff) if random.random() > 0.2 else None
            
            CleaningTask.objects.create(
                room=room,
                assigned_to=assigned,
                cleaning_type=random.choice(['checkout', 'stay_over', 'deep_cleaning']),
                status=random.choice(['pending', 'in_progress', 'completed']),
                priority=random.randint(1, 5),
                notes=f'Limpieza de habitación {room.number}'
            )

    def create_maintenance_tasks(self, rooms, employees):
        """Crea tareas de mantenimiento"""
        maintenance_staff = [e for e in employees if e.role == 'mantenimiento']
        reception_staff = [e for e in employees if e.role in ['recepcionista', 'jefe_recepcion']]
        
        issues = [
            'Aire acondicionado no funciona',
            'Goteo en el baño',
            'Luz del baño parpadeante',
            'Puerta no cierra bien',
            'TV no enciende',
            'Minibar no enfría',
            'Persiana atascada',
            'Grifo con fuga',
        ]
        
        for i in range(12):
            room = random.choice(rooms)
            reported_by = random.choice(reception_staff) if reception_staff else None
            assigned = random.choice(maintenance_staff) if random.random() > 0.3 else None
            
            MaintenanceTask.objects.create(
                room=room,
                reported_by=reported_by.user if reported_by else None,
                assigned_to=assigned,
                title=random.choice(issues),
                description=f'Se reporta problema en habitación {room.number}',
                priority=random.choice(['low', 'medium', 'high', 'urgent']),
                status=random.choice(['pending', 'assigned', 'in_progress', 'completed']),
                resolution='Problema resuelto' if random.random() > 0.5 else ''
            )

    def print_summary(self, employees, rooms, reservations):
        """Imprime un resumen de los datos creados"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('RESUMEN DE DATOS CREADOS'))
        self.stdout.write('='*50)
        
        self.stdout.write(f'\n👥 EMPLEADOS: {len(employees)}')
        for emp in employees[:5]:
            self.stdout.write(f'   • {emp.get_full_name()} - {emp.get_role_display()}')
        self.stdout.write(f'   ... y {len(employees) - 5} más')
        
        self.stdout.write(f'\n🏨 HABITACIONES: {len(rooms)}')
        self.stdout.write(f'   • Por piso: {", ".join([f"Piso {f}: {len([r for r in rooms if r.floor == f])}" for f in [1,2,3,4]])}')
        
        self.stdout.write(f'\n📅 RESERVAS: {len(reservations)}')
        self.stdout.write(f'   • Activas: {len([r for r in reservations if r.status == "checked_in"])}')
        self.stdout.write(f'   • Futuras: {len([r for r in reservations if r.status in ["pending", "confirmed"]])}')
        
        self.stdout.write(f'\n✓ ASISTENCIAS: {Attendance.objects.count()}')
        self.stdout.write(f'✓ PERMISOS: {Leave.objects.count()}')
        self.stdout.write(f'✓ TAREAS DE LIMPIEZA: {CleaningTask.objects.count()}')
        self.stdout.write(f'✓ TAREAS DE MANTENIMIENTO: {MaintenanceTask.objects.count()}')
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('CREDENCIALES DE ACCESO'))
        self.stdout.write('='*50)
        self.stdout.write('\n🔑 Usuarios creados (username / password):')
        credentials = [
            ('director', 'director123', 'Director'),
            ('jefe.recepcion', 'recepcion123', 'Jefe de Recepción'),
            ('ana.recepcion', 'recepcion123', 'Recepcionista'),
            ('jefe.limpieza', 'limpieza123', 'Jefe de Limpieza'),
            ('carmen.limpieza', 'limpieza123', 'Camarera de Piso'),
            ('jefe.mantenimiento', 'mantenimiento123', 'Jefe de Mantenimiento'),
            ('juan.mantenimiento', 'mantenimiento123', 'Mantenimiento'),
            ('rrhh', 'rrhh123', 'RRHH'),
        ]
        
        for username, password, role in credentials:
            self.stdout.write(f'   • {username:20s} / {password:15s} ({role})')
        
        self.stdout.write('\n' + '='*50 + '\n')