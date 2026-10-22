import pytest
from pydantic import ValidationError

from app import services
from app.models import BookingCreate, RoomCreate

pytestmark = pytest.mark.unit


def make_room(**kw):
    data = {
        "nombre": "Lab A",
        "edificio": "Edificio A",
        "capacidad": 30,
        "equipamiento": ["ordenadores"],
    }
    data.update(kw)
    return services.create_room(RoomCreate(**data))


def booking(aula_id, **kw):
    data = {
        "aula_id": aula_id,
        "usuario": "ana",
        "fecha": "2026-10-12",
        "hora_inicio": "10:00",
        "hora_fin": "12:00",
    }
    data.update(kw)
    return BookingCreate(**data)


# ---------- aulas ----------
def test_create_room():
    room = make_room()
    assert room.id == 1
    assert room.nombre == "Lab A"
    assert room.equipamiento == ["ordenadores"]


def test_create_room_ids_are_incremental():
    assert make_room().id == 1
    assert make_room(nombre="Lab B").id == 2


@pytest.mark.parametrize("capacidad", [0, -1, -50])
def test_room_invalid_capacity(capacidad):
    with pytest.raises(ValidationError):
        RoomCreate(nombre="X", edificio="Y", capacidad=capacidad)


def test_room_empty_name():
    with pytest.raises(ValidationError):
        RoomCreate(nombre="", edificio="Y", capacidad=10)


def test_get_room():
    room = make_room()
    assert services.get_room(room.id) == room


def test_get_room_not_found():
    with pytest.raises(services.RoomNotFoundError):
        services.get_room(999)


def test_list_rooms():
    assert services.list_rooms() == []
    make_room()
    make_room(nombre="Lab B")
    assert len(services.list_rooms()) == 2


def test_delete_room():
    room = make_room()
    services.delete_room(room.id)
    with pytest.raises(services.RoomNotFoundError):
        services.get_room(room.id)


def test_delete_room_not_found():
    with pytest.raises(services.RoomNotFoundError):
        services.delete_room(999)


# ---------- validación de reservas (modelo) ----------
def test_booking_valid():
    assert booking(1).hora_inicio == "10:00"


@pytest.mark.parametrize(
    "inicio,fin",
    [("12:00", "10:00"), ("10:00", "10:00")],
)
def test_booking_invalid_hours_order(inicio, fin):
    with pytest.raises(ValidationError):
        booking(1, hora_inicio=inicio, hora_fin=fin)


@pytest.mark.parametrize("hora", ["9:00", "25:00", "10:70", "abc"])
def test_booking_invalid_hour_format(hora):
    with pytest.raises(ValidationError):
        booking(1, hora_inicio=hora)


@pytest.mark.parametrize("fecha", ["2026-13-45", "12/10/2026", "hoy"])
def test_booking_invalid_date(fecha):
    with pytest.raises(ValidationError):
        booking(1, fecha=fecha)


# ---------- reservas (services) ----------
def test_create_booking():
    room = make_room()
    b = services.create_booking(booking(room.id))
    assert b.id == 1
    assert b.aula_id == room.id
    assert b.fecha == "2026-10-12"


def test_create_booking_room_not_found():
    with pytest.raises(services.RoomNotFoundError):
        services.create_booking(booking(999))


@pytest.mark.parametrize(
    "inicio,fin",
    [
        ("11:00", "13:00"),  # solape parcial por el final
        ("09:00", "10:30"),  # solape parcial por el principio
        ("10:30", "11:30"),  # contenida
        ("09:00", "13:00"),  # engloba
        ("10:00", "12:00"),  # idéntica
    ],
)
def test_booking_overlap_rejected(inicio, fin):
    room = make_room()
    services.create_booking(booking(room.id))
    with pytest.raises(services.BookingOverlapError):
        services.create_booking(booking(room.id, hora_inicio=inicio, hora_fin=fin))


@pytest.mark.parametrize(
    "inicio,fin",
    [("12:00", "14:00"), ("08:00", "10:00")],  # pegadas
)
def test_adjacent_bookings_allowed(inicio, fin):
    room = make_room()
    services.create_booking(booking(room.id))
    services.create_booking(booking(room.id, hora_inicio=inicio, hora_fin=fin))
    assert len(services.list_bookings()) == 2


def test_same_hours_other_room_allowed():
    r1, r2 = make_room(), make_room(nombre="Lab B")
    services.create_booking(booking(r1.id))
    services.create_booking(booking(r2.id))
    assert len(services.list_bookings()) == 2


def test_same_hours_other_date_allowed():
    room = make_room()
    services.create_booking(booking(room.id))
    services.create_booking(booking(room.id, fecha="2026-10-13"))
    assert len(services.list_bookings()) == 2


def test_delete_booking():
    room = make_room()
    b = services.create_booking(booking(room.id))
    services.delete_booking(b.id)
    with pytest.raises(services.BookingNotFoundError):
        services.get_booking(b.id)


def test_delete_booking_not_found():
    with pytest.raises(services.BookingNotFoundError):
        services.delete_booking(999)


def test_slot_free_after_delete():
    room = make_room()
    b = services.create_booking(booking(room.id))
    services.delete_booking(b.id)
    services.create_booking(booking(room.id))  # no debe dar solape


def test_delete_room_removes_its_bookings():
    room = make_room()
    services.create_booking(booking(room.id))
    services.delete_room(room.id)
    assert services.list_bookings() == []
