from datetime import datetime

from pydantic import BaseModel


class RoomCreate(BaseModel):
    building: str
    room_number: str
    occupant_count: int = 1
    area_sqft: float | None = None


class RoomOut(RoomCreate):
    id: int

    class Config:
        from_attributes = True


class ReadingCreate(BaseModel):
    room_id: int
    timestamp: datetime
    reading_kwh: float