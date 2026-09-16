from fastapi import (
    APIRouter,
    UploadFile,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

import pandas as pd
import io
import csv

from .. import models
from ..database import get_db


router = APIRouter(
    prefix="/readings",
    tags=["readings"]
)


@router.post("/upload-csv")
async def upload_csv(
    room_id: int,
    file: UploadFile,
    db: Session = Depends(get_db)
):
    content = await file.read()

    # The UCI household dataset is semicolon-delimited and reports
    # average active power in kW every minute. Convert it to hourly energy
    # before writing so a 135 MB source file does not create millions of
    # database rows.
    def clean_column(value: object) -> str:
        return str(value).replace("\ufeff", "").strip().strip('"').strip()

    # Some downloaded copies of this UCI file quote each complete line,
    # meaning normal CSV quoting hides the semicolon delimiters. QUOTE_NONE
    # handles that form and the cleanup below removes the remaining quotes.
    uci_preview = pd.read_csv(
        io.BytesIO(content), sep=";", quoting=csv.QUOTE_NONE, nrows=2
    )
    uci_preview.columns = [clean_column(c) for c in uci_preview.columns]
    uci_columns = {"Date", "Time", "Global_active_power"}
    if uci_columns.issubset(uci_preview.columns):
        df = pd.read_csv(
            io.BytesIO(content), sep=";", quoting=csv.QUOTE_NONE, na_values="?"
        )
        df.columns = [clean_column(c) for c in df.columns]
        for column in df.columns:
            if df[column].dtype == "object":
                df[column] = df[column].astype(str).str.strip().str.strip('"')
        df["timestamp"] = pd.to_datetime(
            df["Date"].astype(str) + " " + df["Time"].astype(str),
            dayfirst=True,
            errors="coerce",
        )
        df["reading_kwh"] = pd.to_numeric(
            df["Global_active_power"], errors="coerce"
        ) / 60.0
        bad_rows = int(df[["timestamp", "reading_kwh"]].isna().any(axis=1).sum())
        df = df.dropna(subset=["timestamp", "reading_kwh"])
        # The source is minute-level; hourly aggregation is sufficient for
        # this product and makes imports/querying much faster.
        df["timestamp"] = df["timestamp"].dt.floor("h")
        df = df.groupby("timestamp", as_index=False)["reading_kwh"].sum()
        source = "uci_household"
    else:
        df = pd.read_csv(io.BytesIO(content))
        source = "csv"

    required_cols = {
        "timestamp",
        "reading_kwh"
    }

    if not required_cols.issubset(df.columns):
        raise HTTPException(
            status_code=400,
            detail=(
                f"CSV must contain columns: "
                f"{required_cols}"
            )
        )

    if "bad_rows" not in locals():
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        bad_rows = int(df["timestamp"].isna().sum())

    df = df.dropna(
        subset=[
            "timestamp",
            "reading_kwh"
        ]
    )

    # Make repeated uploads safe for a room: the UCI file is commonly
    # selected more than once while experimenting with the dashboard.
    existing_timestamps = {
        row.timestamp
        for row in db.query(models.MeterReading.timestamp)
        .filter(models.MeterReading.room_id == room_id)
        .all()
    }
    if existing_timestamps:
        df = df[~df["timestamp"].isin(existing_timestamps)]

    records = [
        models.MeterReading(
            room_id=room_id,
            timestamp=row.timestamp,
            reading_kwh=row.reading_kwh,
            source=source
        )
        for row in df.itertuples()
    ]

    db.bulk_save_objects(records)

    db.commit()

    return {
        "inserted": len(records),
        "skipped_bad_rows": int(bad_rows),
        "format": source,
        "first_timestamp": df["timestamp"].min().isoformat() if len(df) else None,
        "last_timestamp": df["timestamp"].max().isoformat() if len(df) else None,
    }
