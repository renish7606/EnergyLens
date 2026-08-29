from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session

import pandas as pd

from .. import models
from ..database import get_db


router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)


@router.get("/summary")
def consumption_summary(
    room_id: int,
    period: str = Query(
        "D",
        enum=["D", "W", "M"]
    ),
    db: Session = Depends(get_db)
):
    rows = (
        db.query(models.MeterReading)
        .filter(
            models.MeterReading.room_id == room_id
        )
        .all()
    )

    df = pd.DataFrame(
        [
            (r.timestamp, r.reading_kwh)
            for r in rows
        ],
        columns=[
            "timestamp",
            "kwh"
        ]
    )

    if df.empty:
        return []

    df = (
        df
        .set_index("timestamp")
        .sort_index()
    )

    resampled = df.resample(period).sum()

    return resampled.reset_index().to_dict(
        orient="records"
    )