import psycopg
from fastapi import FastAPI, HTTPException

from app.db import check_connection
from app.routers import bookings, rooms

app = FastAPI(title="SmartCampus")
app.include_router(rooms.router)
app.include_router(bookings.router)


@app.get("/health")
def health():
    """Liveness: el proceso responde. No toca la base de datos."""
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    """Readiness: comprueba la comunicación backend -> base de datos."""
    try:
        check_connection()
    except psycopg.Error:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")
    return {"status": "ok", "database": "ok"}
