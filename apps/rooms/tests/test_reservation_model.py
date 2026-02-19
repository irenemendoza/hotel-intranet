from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.rooms.models import Reservation, Room, RoomType


class ReservationModelTest(TestCase):
    """Tests para el modelo Reservation"""

    def setUp(self):
        """Configuración inicial"""
        self.room_type = RoomType.objects.create(name="Double", code="DBL", capacity=2)

        self.room = Room.objects.create(
            number="213",
            floor=2,
            room_type=self.room_type,
        )

    def test_reservation_number_auto_generated(self):
        """El número de reserva debe generarse automáticamente"""
        reservation = Reservation.objects.create(
            room=self.room,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=2),
            guest_first_name="Manuel",
            guest_last_name="Muñoz",
            guest_email="manuelm@mail.com",
            guest_phone="3456345",
            room_rate=Decimal("50.00"),
        )

        self.assertIsNotNone(reservation.reservation_number)

    def test_checkout_date_must_be_after_checkin(self):
        """La fecha del check-out debe ser posterior a la del chek-in"""
        reservation = Reservation(
            room=self.room,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=-2),
            guest_first_name="Manuel",
            guest_last_name="Muñoz",
            guest_email="manuelm@mail.com",
            guest_phone="3456345",
            room_rate=Decimal("50.00"),
        )

        with self.assertRaises(ValidationError) as context:
            reservation.full_clean()

        self.assertIn("check_out_date", context.exception.message_dict)

    def test_total_amount_calculation(self):
        """El total debe calcularse automáticamente como: (días * tarifa)"""
        check_in = date.today()
        check_out = date.today() + timedelta(days=2)
        room_rate = Decimal("50.00")

        reservation = Reservation.objects.create(
            room=self.room,
            check_in_date=check_in,
            check_out_date=check_out,
            guest_first_name="Manuel",
            guest_last_name="Muñoz",
            guest_email="manuelm@mail.com",
            guest_phone="3456345",
            room_rate=room_rate,
        )

        days = (check_out - check_in).days
        expected_total = Decimal(Decimal(days) * reservation.room_rate)
        self.assertEqual(reservation.total_amount, expected_total)

    def test_payment_status_update(self):
        """El status de pago debe actualizarse según el monto pagado"""
        reservation = Reservation.objects.create(
            room=self.room,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=2),
            guest_first_name="Manuel",
            guest_last_name="Muñoz",
            guest_email="manuelm@mail.com",
            guest_phone="3456345",
            room_rate=Decimal("50.00"),
            total_amount=Decimal("100.00"),
        )

        # Sin pago
        self.assertEqual(
            reservation.payment_status, Reservation.PaymentStatusChoices.UNPAID
        )

        # Pago parcial
        reservation.paid_amount = Decimal("50.00")
        reservation.save()
        self.assertEqual(
            reservation.payment_status, Reservation.PaymentStatusChoices.PARTIAL
        )

        # Pago completo
        reservation.paid_amount = Decimal("100.00")
        reservation.save()
        self.assertEqual(
            reservation.payment_status, Reservation.PaymentStatusChoices.PAID
        )

    def test_room_availability_validation(self):
        """No se puede crear una reserva si la habitación ya está reservada en esas fechas"""
        # Primera reserva
        Reservation.objects.create(
            room=self.room,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=2),
            guest_first_name="Manuel",
            guest_last_name="Muñoz",
            guest_email="manuelm@mail.com",
            guest_phone="3456345",
            room_rate=Decimal("50.00"),
            status=Reservation.StatusChoices.CONFIRMED,
        )

        # Segunda reserva
        reservation2 = Reservation(
            room=self.room,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=2),
            guest_first_name="María",
            guest_last_name="Martínez",
            guest_email="mariam@mail.com",
            guest_phone="3434545",
            room_rate=Decimal("50.00"),
        )

        with self.assertRaises(ValidationError) as context:
            reservation2.full_clean()

        self.assertIn("room", context.exception.message_dict)

        # Verificar el mensaje
        error_message = str(context.exception.message_dict["room"][0])
        self.assertIn("not available", error_message.lower())

    def test_night_calculation(self):
        """El método nights() debe calcular correctamente el número de noches"""
        reservation = Reservation.objects.create(
            room=self.room,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=2),
            guest_first_name="Manuel",
            guest_last_name="Muñoz",
            guest_email="manuelm@mail.com",
            guest_phone="3456345",
            room_rate=Decimal("50.00"),
            status=Reservation.StatusChoices.CONFIRMED,
        )

        nights = reservation.nights

        self.assertEqual(nights, 2)
