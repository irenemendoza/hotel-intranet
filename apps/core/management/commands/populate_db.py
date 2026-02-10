from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from apps.employees.models import Department, UserProfile
from apps.rooms.models import Room, RoomType


class Command(BaseCommand):
    help = "Populate database with sample data"

    def handle(self, *args, **kwargs):
        # Crear departamentos
        self.stdout.write(self.style.WARNING("Creando departamentos..."))

        departments_data = [
            {"name": "Dirección", "code": "DIR"},
            {"name": "Recepción", "code": "REC"},
            {"name": "Limpieza", "code": "LIM"},
            {"name": "Mantenimiento", "code": "MAN"},
            {"name": "Restaurante", "code": "RES"},
        ]

        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(**dept_data)
            if created:
                self.stdout.write(f"  ✓ Departamento creado: {dept.name}")
            else:
                self.stdout.write(f"  - Departamento ya existe: {dept.name}")

        self.stdout.write(self.style.SUCCESS("Departamentos listos\n"))

        # Crear tipos de habitación
        self.stdout.write(self.style.WARNING("Creando tipos de habitación..."))

        room_types_data = [
            {"name": "Individual", "code": "IND", "capacity": 1, "base_price": 50.00},
            {"name": "Doble", "code": "DBL", "capacity": 2, "base_price": 80.00},
            {"name": "Suite", "code": "SUI", "capacity": 4, "base_price": 150.00},
        ]

        for rt_data in room_types_data:
            room_type, created = RoomType.objects.get_or_create(**rt_data)
            if created:
                self.stdout.write(f"  ✓ Tipo creado: {room_type.name}")
            else:
                self.stdout.write(f"  - Tipo ya existe: {room_type.name}")

        self.stdout.write(self.style.SUCCESS("Tipos de habitación listos\n"))

        # Crear algunas habitaciones
        self.stdout.write(self.style.WARNING("Creando habitaciones..."))

        room_types = list(RoomType.objects.all())
        rooms_created = 0
        rooms_existing = 0

        for floor in range(1, 4):
            for num in range(1, 6):
                room_number = f"{floor}0{num}"
                room, created = Room.objects.get_or_create(
                    number=room_number,
                    defaults={
                        "floor": floor,
                        "room_type": room_types[(floor + num) % len(room_types)],
                    },
                )
                if created:
                    rooms_created += 1
                else:
                    rooms_existing += 1

        self.stdout.write(f"  ✓ Habitaciones creadas: {rooms_created}")
        self.stdout.write(f"  - Habitaciones ya existentes: {rooms_existing}")
        self.stdout.write(self.style.SUCCESS("✅ Habitaciones listas\n"))

        # Crear usuarios de prueba
        self.stdout.write(self.style.WARNING("Creando usuarios de prueba..."))

        users_data = [
            {
                "username": "director",
                "email": "director@levantehotel.com",
                "first_name": "Carlos",
                "last_name": "Martínez",
                "dept_code": "DIR",
            },
            {
                "username": "recepcionista1",
                "email": "recep1@levantehotel.com",
                "first_name": "Ana",
                "last_name": "García",
                "dept_code": "REC",
            },
            {
                "username": "recepcionista2",
                "email": "recep2@levantehotel.com",
                "first_name": "Luis",
                "last_name": "Fernández",
                "dept_code": "REC",
            },
            {
                "username": "camarera1",
                "email": "limpieza1@levantehotel.com",
                "first_name": "María",
                "last_name": "López",
                "dept_code": "LIM",
            },
            {
                "username": "camarera2",
                "email": "limpieza2@levantehotel.com",
                "first_name": "Carmen",
                "last_name": "Ruiz",
                "dept_code": "LIM",
            },
            {
                "username": "mantenimiento1",
                "email": "mant1@levantehotel.com",
                "first_name": "Juan",
                "last_name": "Pérez",
                "dept_code": "MAN",
            },
            {
                "username": "mantenimiento2",
                "email": "mant2@levantehotel.com",
                "first_name": "Pedro",
                "last_name": "Sánchez",
                "dept_code": "MAN",
            },
            {
                "username": "restaurante1",
                "email": "rest1@levantehotel.com",
                "first_name": "Laura",
                "last_name": "Torres",
                "dept_code": "RES",
            },
        ]

        users_created = 0
        users_existing = 0

        for user_data in users_data:
            dept_code = user_data.pop("dept_code")

            # Crear o obtener usuario
            user, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults={
                    "email": user_data["email"],
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                },
            )

            if created:
                # Establecer contraseña demo
                user.set_password("demo123")
                user.save()

                # Crear perfil de usuario
                department = Department.objects.get(code=dept_code)
                UserProfile.objects.create(
                    user=user,
                    department=department,
                    employee_number=f"EMP{user.id:04d}",
                )

                users_created += 1
                self.stdout.write(
                    f"  ✓ Usuario creado: {user.username} "
                    f"({user.first_name} {user.last_name}) - {department.name}"
                )
            else:
                users_existing += 1
                self.stdout.write(f"  - Usuario ya existe: {user.username}")

        self.stdout.write(f"\n  Total usuarios creados: {users_created}")
        self.stdout.write(f"  Total usuarios ya existentes: {users_existing}")
        self.stdout.write(self.style.SUCCESS("✅ Usuarios de prueba listos\n"))

        # RESUMEN FINAL

        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("✅ BASE DE DATOS POBLADA EXITOSAMENTE"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write("\n📋 CREDENCIALES DE PRUEBA:")
        self.stdout.write("   Usuario: director | Contraseña: demo123")
        self.stdout.write("   Usuario: recepcionista1 | Contraseña: demo123")
        self.stdout.write("   Usuario: camarera1 | Contraseña: demo123")
        self.stdout.write("   Usuario: mantenimiento1 | Contraseña: demo123")
        self.stdout.write("\n🔗 Accede en: http://127.0.0.1:8000/login/")
        self.stdout.write(self.style.SUCCESS("=" * 50 + "\n"))
