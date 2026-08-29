from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas, models
from ..database import get_db


router = APIRouter(
    prefix="/rooms",
    tags=["rooms"]
)


@router.post(
    "/",
    response_model=schemas.RoomOut
)
def create_room(
    room: schemas.RoomCreate,
    db: Session = Depends(get_db)
):
    db_room = models.Room(
        **room.model_dump()
    )

    db.add(db_room)
    db.commit()
    db.refresh(db_room)

    return db_room


@router.get(
    "/",
    response_model=list[schemas.RoomOut]
)
def list_rooms(
    db: Session = Depends(get_db)
):
    return db.query(models.Room).all()