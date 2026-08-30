import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..services.analytics import load_readings_df

from ..services.anomaly import detect_anomalies_iqr

from ..services.billing import estimate_bill

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
    
@router.get("/trend")
def trend(
    room_id: int,
    db: Session = Depends(get_db)
):
    df = load_readings_df(
        db,
        room_id
    )

    if df.empty:
        return []

    daily = df.resample("D").sum()

    rolling_7d = (
        daily["kwh"]
        .rolling(7)
        .mean()
    )

    pct_change = (
        daily["kwh"]
        .pct_change()
        * 100
    )

    daily["rolling_7d"] = (
        rolling_7d.astype(object)
        .where(rolling_7d.notna(), None)
    )
    daily["pct_change"] = (
        pct_change
        .replace([float("inf"), float("-inf")], None)
        .astype(object)
        .where(pct_change.notna(), None)
    )

    return (
        daily
        .reset_index()
        .to_dict(orient="records")
    )


@router.get("/compare")
def compare_rooms(
    db: Session = Depends(get_db)
):
    rooms = db.query(models.Room).all()

    results = []

    for room in rooms:

        df = load_readings_df(
            db,
            room.id
        )

        if df.empty:
            total_kwh = 0
        else:
            total_kwh = df["kwh"].sum()

        per_occupant = (
            total_kwh /
            max(room.occupant_count, 1)
        )

        results.append(
            {
                "room": (
                    f"{room.building}-"
                    f"{room.room_number}"
                ),
                "total_kwh": round(
                    total_kwh,
                    2
                ),
                "kwh_per_occupant": round(
                    per_occupant,
                    2
                )
            }
        )

    return sorted(
        results,
        key=lambda r: r["kwh_per_occupant"],
        reverse=True
    )
    
    
@router.get("/anomalies")
def anomalies(
    room_id: int,
    db: Session = Depends(get_db)
):
    df = load_readings_df(
        db,
        room_id
    )

    if df.empty:
        return []

    daily = df.resample("D").sum()

    result = detect_anomalies_iqr(
        daily["kwh"]
    )

    return (
        result
        .reset_index()
        .to_dict(orient="records")
    )
    
    
@router.get("/peak")
def peak_usage(
    room_id: int,
    db: Session = Depends(get_db)
):
    df = load_readings_df(
        db,
        room_id,
        keep_raw_timestamp=True
    )

    if df.empty:
        return []

    df["hour"] = (
        df["timestamp"]
        .dt.hour
    )

    df["day_of_week"] = (
        df["timestamp"]
        .dt.day_name()
    )

    pivot = df.pivot_table(
        values="kwh",
        index="day_of_week",
        columns="hour",
        aggfunc="mean",
        fill_value=0
    )

    return (
        pivot
        .reset_index()
        .to_dict(orient="records")
    )
    
@router.get("/bill")
def bill_estimate(
    room_id: int,
    db: Session = Depends(get_db)
):
    df = load_readings_df(
        db,
        room_id
    )

    if df.empty:
        return {
            "total_kwh": 0,
            "estimated_bill": 0
        }

    total_kwh = df["kwh"].sum()

    bill = estimate_bill(
        total_kwh
    )

    return {
        "total_kwh": round(
            total_kwh,
            2
        ),
        "estimated_bill": bill
    }