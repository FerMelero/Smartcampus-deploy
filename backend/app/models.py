from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator


class RoomCreate(BaseModel):
    nombre: str = Field(min_length=1)
    edificio: str = Field(min_length=1)
    capacidad: int = Field(gt=0)  # mayor a 0
    equipamiento: list[str] = Field(default_factory=list)


class Room(RoomCreate):
    id: int


HORA_PATTERN = r"^([01]\d|2[0-3]):[0-5]\d$"  # regex para validar hora HH:MM


class BookingCreate(BaseModel):
    aula_id: int = Field(gt=0)
    usuario: str = Field(min_length=1)
    fecha: str  # YYYY-MM-DD
    hora_inicio: str = Field(pattern=HORA_PATTERN)
    hora_fin: str = Field(pattern=HORA_PATTERN)

    @field_validator("fecha")
    @classmethod
    def validar_fecha(cls, v: str) -> str:
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("La fecha debe tener formato YYYY-MM-DD")
        return v

    @model_validator(mode="after")
    def validar_horas(self):
        if self.hora_inicio >= self.hora_fin:
            raise ValueError("hora_inicio debe ser anterior a hora_fin")
        return self


class Booking(BookingCreate):
    id: int
