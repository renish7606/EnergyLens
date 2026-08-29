from fastapi import (
    APIRouter,
    UploadFile,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

import pandas as pd
import io

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

    df = pd.read_csv(
        io.BytesIO(content)
    )

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

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    bad_rows = df["timestamp"].isna().sum()

    df = df.dropna(
        subset=[
            "timestamp",
            "reading_kwh"
        ]
    )

    records = [
        models.MeterReading(
            room_id=room_id,
            timestamp=row.timestamp,
            reading_kwh=row.reading_kwh,
            source="csv"
        )
        for row in df.itertuples()
    ]

    db.bulk_save_objects(records)

    db.commit()

    return {
        "inserted": len(records),
        "skipped_bad_rows": int(bad_rows)
    }