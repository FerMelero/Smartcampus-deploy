import pytest

pytestmark = pytest.mark.integration

ROOM = {
    "nombre": "Laboratorio de Robótica",
    "edificio": "Edificio A",
    "capacidad": 30,
    "equipamiento": ["ordenadores", "robots", "impresora 3D"],
}


def test_list_rooms_empty(client):
    r = client.get("/rooms")
    assert r.status_code == 200
    assert r.json() == []


def test_create_room(client):
    r = client.post("/rooms", json=ROOM)
    assert r.status_code == 201
    assert r.json() == {"id": 1, **ROOM}


def test_create_room_without_equipment(client):
    data = {k: v for k, v in ROOM.items() if k != "equipamiento"}
    r = client.post("/rooms", json=data)
    assert r.status_code == 201
    assert r.json()["equipamiento"] == []


def test_get_room(client):
    client.post("/rooms", json=ROOM)
    r = client.get("/rooms/1")
    assert r.status_code == 200
    assert r.json()["nombre"] == ROOM["nombre"]


def test_list_rooms(client):
    client.post("/rooms", json=ROOM)
    client.post("/rooms", json={**ROOM, "nombre": "Aula Magna"})
    r = client.get("/rooms")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_room_not_found(client):
    r = client.get("/rooms/999")
    assert r.status_code == 404


@pytest.mark.parametrize("capacidad", [0, -5])
def test_create_room_invalid_capacity(client, capacidad):
    r = client.post("/rooms", json={**ROOM, "capacidad": capacidad})
    assert r.status_code == 422


def test_create_room_empty_name(client):
    r = client.post("/rooms", json={**ROOM, "nombre": ""})
    assert r.status_code == 422


def test_create_room_missing_field(client):
    data = {k: v for k, v in ROOM.items() if k != "edificio"}
    r = client.post("/rooms", json=data)
    assert r.status_code == 422


def test_get_room_invalid_id(client):
    r = client.get("/rooms/abc")
    assert r.status_code == 422


def test_delete_room(client):
    client.post("/rooms", json=ROOM)
    r = client.delete("/rooms/1")
    assert r.status_code == 204
    assert client.get("/rooms/1").status_code == 404


def test_delete_room_not_found(client):
    r = client.delete("/rooms/999")
    assert r.status_code == 404
