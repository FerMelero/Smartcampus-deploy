import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app

# Los tests usan el Postgres indicado por DB_* (ver .env.example / docker-compose).
# El esquema se crea desde el mismo init.sql que usa el contenedor de la base de datos.
INIT_SQL = Path(
    os.getenv("INIT_SQL", Path(__file__).resolve().parents[2] / "database" / "init.sql")
)


@pytest.fixture(scope="session", autouse=True)
def schema():
    with get_connection() as conn:
        conn.execute(INIT_SQL.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def clean_db(schema):
    """Cada test empieza con las tablas vacías y los ids reiniciados a 1."""
    with get_connection() as conn:
        conn.execute("TRUNCATE rooms, bookings RESTART IDENTITY CASCADE")


@pytest.fixture
def client():
    return TestClient(app)
