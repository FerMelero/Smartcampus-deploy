from fastapi import APIRouter, HTTPException, Response, status

from app import services
from app.models import Room, RoomCreate

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[Room])
def list_rooms():
    return services.list_rooms()


@router.get("/{room_id}", response_model=Room)
def get_room(room_id: int):
    try:
        return services.get_room(room_id)
    except services.RoomNotFoundError:
        raise HTTPException(status_code=404, detail="Aula no encontrada")


@router.post("", response_model=Room, status_code=status.HTTP_201_CREATED)
def create_room(data: RoomCreate):
    return services.create_room(data)


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: int):
    try:
        services.delete_room(room_id)
    except services.RoomNotFoundError:
        raise HTTPException(status_code=404, detail="Aula no encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
