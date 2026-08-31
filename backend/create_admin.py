from getpass import getpass

from app.database import SessionLocal
from app.models import AdminUser
from app.auth import hash_password


username = input(
    "Admin username: "
)

password = getpass(
    "Admin password: "
)


db = SessionLocal()

try:
    existing = (
        db.query(AdminUser)
        .filter(
            AdminUser.username == username
        )
        .first()
    )

    if existing:
        print("Admin already exists.")
    else:
        admin = AdminUser(
            username=username,
            hashed_password=hash_password(password)
        )

        db.add(admin)
        db.commit()

        print(
            "Admin user created successfully."
        )

finally:
    db.close()