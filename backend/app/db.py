import psycopg
from psycopg.rows import dict_row

from app.config import get_db_dsn


def get_connection() -> psycopg.Connection:
    """Nueva conexión por operación. Usar con `with`: confirma al salir y siempre cierra."""
    return psycopg.connect(get_db_dsn(), row_factory=dict_row, connect_timeout=5)


def check_connection() -> None:
    """Lanza una excepción si no se puede hablar con la base de datos."""
    with get_connection() as conn:
        conn.execute("SELECT 1")
