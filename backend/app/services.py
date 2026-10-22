from app.db import get_connection
from app.models import Booking, BookingCreate, Room, RoomCreate

# Las horas se devuelven como HH:MM y la fecha como YYYY-MM-DD, igual que en la API.
ROOM_COLS = "id, nombre, edificio, capacidad, equipamiento"
BOOKING_COLS = (
    "id, aula_id, usuario, fecha::text AS fecha, "
    "to_char(hora_inicio, 'HH24:MI') AS hora_inicio, "
    "to_char(hora_fin, 'HH24:MI') AS hora_fin"
)


class RoomNotFoundError(Exception):
    pass


class BookingNotFoundError(Exception):
    pass


class BookingOverlapError(Exception):
    pass


# ---------- aulas ----------
def create_room(data: RoomCreate) -> Room:
    with get_connection() as conn:
        row = conn.execute(
            f"INSERT INTO rooms (nombre, edificio, capacidad, equipamiento) "
            f"VALUES (%s, %s, %s, %s) RETURNING {ROOM_COLS}",
            (data.nombre, data.edificio, data.capacidad, data.equipamiento),
        ).fetchone()
    return Room(**row)


def list_rooms() -> list[Room]:
    with get_connection() as conn:
        rows = conn.execute(f"SELECT {ROOM_COLS} FROM rooms ORDER BY id").fetchall()
    return [Room(**r) for r in rows]


def get_room(room_id: int) -> Room:
    with get_connection() as conn:
        row = conn.execute(f"SELECT {ROOM_COLS} FROM rooms WHERE id = %s", (room_id,)).fetchone()
    if row is None:
        raise RoomNotFoundError(room_id)
    return Room(**row)


def delete_room(room_id: int) -> None:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM rooms WHERE id = %s", (room_id,))
        if cur.rowcount == 0:
            raise RoomNotFoundError(room_id)


# ---------- reservas ----------
def create_booking(data: BookingCreate) -> Booking:
    # Todo en una transacción. FOR UPDATE bloquea la fila del aula, así dos reservas
    # simultáneas para la misma aula se serializan y no pueden solaparse.
    with get_connection() as conn:
        room = conn.execute("SELECT id FROM rooms WHERE id = %s FOR UPDATE", (data.aula_id,))
        if room.fetchone() is None:
            raise RoomNotFoundError(data.aula_id)

        overlap = conn.execute(
            "SELECT 1 FROM bookings "
            "WHERE aula_id = %s AND fecha = %s AND %s < hora_fin AND %s > hora_inicio "
            "LIMIT 1",
            (data.aula_id, data.fecha, data.hora_inicio, data.hora_fin),
        ).fetchone()
        if overlap is not None:
            raise BookingOverlapError()

        row = conn.execute(
            f"INSERT INTO bookings (aula_id, usuario, fecha, hora_inicio, hora_fin) "
            f"VALUES (%s, %s, %s, %s, %s) RETURNING {BOOKING_COLS}",
            (data.aula_id, data.usuario, data.fecha, data.hora_inicio, data.hora_fin),
        ).fetchone()
    return Booking(**row)


def list_bookings() -> list[Booking]:
    with get_connection() as conn:
        rows = conn.execute(f"SELECT {BOOKING_COLS} FROM bookings ORDER BY id").fetchall()
    return [Booking(**r) for r in rows]


def get_booking(booking_id: int) -> Booking:
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT {BOOKING_COLS} FROM bookings WHERE id = %s", (booking_id,)
        ).fetchone()
    if row is None:
        raise BookingNotFoundError(booking_id)
    return Booking(**row)


def delete_booking(booking_id: int) -> None:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
        if cur.rowcount == 0:
            raise BookingNotFoundError(booking_id)
