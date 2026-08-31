from fastapi import (
    APIRouter,
    HTTPException,
    Depends
)

from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session

from ..auth import (
    verify_password,
    create_access_token
)

from ..database import get_db
from .. import models


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post("/login")
def login(
    credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    admin = (
        db.query(models.AdminUser)
        .filter(
            models.AdminUser.username ==
            credentials.username
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not verify_password(
        credentials.password,
        admin.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    token = create_access_token(
        {
            "sub": admin.username
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }