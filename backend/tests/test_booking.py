import pytest

pytestmark = pytest.mark.integration

ROOM = {"nombre": "Lab A", "edificio": "Edificio A", "capacidad": 30}


def booking(aula_id=1, **kw):
    data = {
        "aula_id": aula_id,
        "usuario": "ana",
        "fecha": "2026-10-12",
        "hora_inicio": "10:00",
        "hora_fin": "12:00",
    }
    data.update(kw)
    return data


@pytest.fixture
def room(client):
    return client.post("/rooms", json=ROOM).json()


def test_list_bookings_empty(client):
    r = client.get("/bookings")
    assert r.status_code == 200
    assert r.json() == []


def test_create_booking(client, room):
    r = client.post("/bookings", json=booking(room["id"]))
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1
    assert body["aula_id"] == room["id"]
    assert body["hora_inicio"] == "10:00"


def test_list_bookings(client, room):
    client.post("/bookings", json=booking(room["id"]))
    client.post("/bookings", json=booking(room["id"], hora_inicio="12:00", hora_fin="13:00"))
    r = client.get("/bookings")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_create_booking_room_not_found(client):
    r = client.post("/bookings", json=booking(999))
    assert r.status_code == 404


@pytest.mark.parametrize(
    "inicio,fin",
    [("12:00", "10:00"), ("10:00", "10:00")],
)
def test_create_booking_invalid_hours(client, room, inicio, fin):
    r = client.post("/bookings", json=booking(room["id"], hora_inicio=inicio, hora_fin=fin))
    assert r.status_code == 422


@pytest.mark.parametrize("hora", ["9:00", "25:00", "10:70"])
def test_create_booking_invalid_hour_format(client, room, hora):
    r = client.post("/bookings", json=booking(room["id"], hora_inicio=hora))
    assert r.status_code == 422


def test_create_booking_invalid_date(client, room):
    r = client.post("/bookings", json=booking(room["id"], fecha="2026-13-45"))
    assert r.status_code == 422


def test_create_booking_missing_field(client, room):
    data = booking(room["id"])
    del data["usuario"]
    r = client.post("/bookings", json=data)
    assert r.status_code == 422


@pytest.mark.parametrize(
    "inicio,fin",
    [("11:00", "13:00"), ("09:00", "10:30"), ("10:30", "11:30"), ("10:00", "12:00")],
)
def test_create_booking_overlap(client, room, inicio, fin):
    client.post("/bookings", json=booking(room["id"]))
    r = client.post("/bookings", json=booking(room["id"], hora_inicio=inicio, hora_fin=fin))
    assert r.status_code == 409


@pytest.mark.parametrize("inicio,fin", [("12:00", "14:00"), ("08:00", "10:00")])
def test_adjacent_bookings_allowed(client, room, inicio, fin):
    client.post("/bookings", json=booking(room["id"]))
    r = client.post("/bookings", json=booking(room["id"], hora_inicio=inicio, hora_fin=fin))
    assert r.status_code == 201


def test_same_hours_other_room(client, room):
    other = client.post("/rooms", json={**ROOM, "nombre": "Lab B"}).json()
    client.post("/bookings", json=booking(room["id"]))
    r = client.post("/bookings", json=booking(other["id"]))
    assert r.status_code == 201


def test_same_hours_other_date(client, room):
    client.post("/bookings", json=booking(room["id"]))
    r = client.post("/bookings", json=booking(room["id"], fecha="2026-10-13"))
    assert r.status_code == 201


def test_delete_booking(client, room):
    client.post("/bookings", json=booking(room["id"]))
    r = client.delete("/bookings/1")
    assert r.status_code == 204
    assert client.get("/bookings").json() == []


def test_delete_booking_not_found(client):
    r = client.delete("/bookings/999")
    assert r.status_code == 404


def test_slot_free_after_delete(client, room):
    client.post("/bookings", json=booking(room["id"]))
    client.delete("/bookings/1")
    r = client.post("/bookings", json=booking(room["id"]))
    assert r.status_code == 201


def test_delete_room_removes_its_bookings(client, room):
    client.post("/bookings", json=booking(room["id"]))
    client.delete(f"/rooms/{room['id']}")
    assert client.get("/bookings").json() == []
