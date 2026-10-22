from fastapi import APIRouter, HTTPException, Response, status

from app import services
from app.models import Booking, BookingCreate

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("", response_model=list[Booking])
def list_bookings():
    return services.list_bookings()


@router.get("/{booking_id}", response_model=Booking)
def get_booking(booking_id: int):
    try:
        return services.get_booking(booking_id)
    except services.BookingNotFoundError:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")


@router.post("", response_model=Booking, status_code=status.HTTP_201_CREATED)
def create_booking(data: BookingCreate):
    try:
        return services.create_booking(data)
    except services.RoomNotFoundError:
        raise HTTPException(status_code=404, detail="Aula no encontrada")
    except services.BookingOverlapError:
        raise HTTPException(status_code=409, detail="Ya existe una reserva solapada para esa aula")


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: int):
    try:
        services.delete_booking(booking_id)
    except services.BookingNotFoundError:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
