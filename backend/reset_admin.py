from getpass import getpass

from app.auth import hash_password
from app.database import SessionLocal
from app.models import AdminUser


username = input("Admin username to reset: ").strip()
password = getpass("New admin password: ")
confirmation = getpass("Confirm new password: ")

if not password or password != confirmation:
    raise SystemExit("Passwords are empty or do not match.")

db = SessionLocal()
try:
    admin = (
        db.query(AdminUser)
        .filter(AdminUser.username == username)
        .first()
    )
    if not admin:
        raise SystemExit(f"Admin user '{username}' does not exist.")

    admin.hashed_password = hash_password(password)
    db.commit()
    print("Admin password reset successfully.")
finally:
    db.close()
