from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.rooms.models import Reservation, Room, RoomType


class RoomModelTest(TestCase):
    """Test para el modelo Room"""

    def setUp(self):
        """Configuración inicial"""

        self.room_type = RoomType.objects.create(
            name="Double",
            code="DBL",
            capacity=2,
        )

    def test_room_number_unique(self):
        """Los números de las habitaciones deben ser únicos"""
        Room.objects.create(
            number="202",
            floor=2,
            room_type=self.room_type,
        )
        # Creación de nueva habitación con mismo número
        room2 = Room(
            number="202",
            floor=3,
            room_type=self.room_type,
        )

        with self.assertRaises(ValidationError) as context:
            room2.full_clean()

        self.assertIn("number", context.exception.message_dict)

    def test_is_occupied_method(self):
        """El método is_occupied() debe indicar si la habitación está ocupada"""
        room = Room.objects.create(
            number="202",
            floor=2,
            room_type=self.room_type,
        )

        # Sin reserva activa
        self.assertFalse(room.is_occupied())

        # Con reserva activa
        check_in = date.today() - timedelta(days=1)
        check_out = date.today() + timedelta(days=2)
        Reservation.objects.create(
            room=room,
            check_in_date=check_in,
            check_out_date=check_out,
            guest_first_name="Paula",
            guest_last_name="García",
            guest_email="paulag@mail.com",
            guest_phone="948599875",
            room_rate=Decimal("100.00"),
            status=Reservation.StatusChoices.CHECKED_IN,
            actual_check_in=timezone.now() - timedelta(days=1),
        )

        self.assertTrue(room.is_occupied())
