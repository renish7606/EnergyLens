import importlib

import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..services.analytics import load_readings_df

from ..services.anomaly import detect_anomalies_iqr

from ..services.billing import estimate_bill

from pydantic import BaseModel

from ..auth import get_current_admin


def _forecast_with_backtest(*args, **kwargs):
    try:
        forecast_module = importlib.import_module("app.services.forcasting")
    except ModuleNotFoundError:  # pragma: no cover - fallback for different package layouts
        forecast_module = importlib.import_module("..services.forcasting", __package__)

    return forecast_module.forecast_with_backtest(*args, **kwargs)


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
    
@router.get("/forecast")
def forecast(
    room_id: int,
    forecast_days: int = 7,
    db: Session = Depends(get_db)
):
    df = load_readings_df(
        db,
        room_id
    )

    if df.empty:
        return {
            "forecast": {},
            "backtest_mape_percent": None
        }

    daily = df.resample("D").sum()

    daily_series = daily["kwh"]

    try:
        result = _forecast_with_backtest(
            daily_series,
            forecast_days=forecast_days
        )
    except ValueError as exc:
        return {
            "error": str(exc)
        }

    return result



@router.get("/alert-check")
def check_alert(
    room_id: int,
    db: Session = Depends(get_db)
):
    alert = (
        db.query(models.Alert)
        .filter(
            models.Alert.room_id == room_id
        )
        .first()
    )

    df = load_readings_df(
        db,
        room_id
    )

    if df.empty:
        return {
            "current_total": 0,
            "projected_month_total": 0,
            "limit": (
                alert.monthly_limit_kwh
                if alert else None
            ),
            "will_exceed": False
        }

    days_elapsed = (
        df.index.max() -
        df.index.min()
    ).days + 1

    days_in_month = 30

    total_kwh = df["kwh"].sum()

    projected = (
        total_kwh /
        max(days_elapsed, 1)
    ) * days_in_month

    return {
        "current_total": round(
            total_kwh,
            2
        ),
        "projected_month_total": round(
            projected,
            2
        ),
        "limit": (
            alert.monthly_limit_kwh
            if alert else None
        ),
        "will_exceed": bool(
            alert and
            projected >
            alert.monthly_limit_kwh
        )
    }
    
    
class AlertCreate(BaseModel):
    room_id: int
    monthly_limit_kwh: float
    
@router.post("/alerts")
def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    alert = models.Alert(
        room_id=alert_data.room_id,
        monthly_limit_kwh=alert_data.monthly_limit_kwh
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return {
        "id": alert.id,
        "room_id": alert.room_id,
        "monthly_limit_kwh": alert.monthly_limit_kwh,
        "created_by": current_admin
    }