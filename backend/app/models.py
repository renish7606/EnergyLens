from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import relationship

from .database import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    building = Column(
        String,
        index=True
    )

    room_number = Column(
        String
    )

    occupant_count = Column(
        Integer,
        default=1
    )

    area_sqft = Column(
        Float,
        nullable=True
    )

    readings = relationship(
        "MeterReading",
        back_populates="room"
    )


class MeterReading(Base):
    __tablename__ = "meter_readings"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    room_id = Column(
        Integer,
        ForeignKey("rooms.id")
    )

    timestamp = Column(
        DateTime,
        index=True
    )

    reading_kwh = Column(
        Float
    )

    source = Column(
        String,
        default="manual"
    )

    room = relationship(
        "Room",
        back_populates="readings"
    )


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    room_id = Column(
        Integer,
        ForeignKey("rooms.id")
    )

    monthly_limit_kwh = Column(
        Float
    )

    triggered_at = Column(
        DateTime,
        nullable=True
    )


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        unique=True,
        index=True
    )

    hashed_password = Column(
        String
    )