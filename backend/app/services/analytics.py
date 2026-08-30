import pandas as pd

from sqlalchemy.orm import Session

from .. import models


def load_readings_df(
    db: Session,
    room_id: int,
    keep_raw_timestamp: bool = False
) -> pd.DataFrame:

    rows = (
        db.query(models.MeterReading)
        .filter(
            models.MeterReading.room_id == room_id
        )
        .order_by(
            models.MeterReading.timestamp
        )
        .all()
    )

    df = pd.DataFrame(
        [
            {
                "timestamp": row.timestamp,
                "kwh": row.reading_kwh
            }
            for row in rows
        ]
    )

    if df.empty:
        return df

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    if not keep_raw_timestamp:
        df = df.set_index("timestamp")

    return df