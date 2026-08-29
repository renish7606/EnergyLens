from fastapi import FastAPI

from .routers import rooms
from .routers import readings
from .routers import analytics


app = FastAPI(
    title="EnergyLens API",
    description="Energy consumption analytics backend",
    version="1.0.0"
)


app.include_router(
    rooms.router
)

app.include_router(
    readings.router
)

app.include_router(
    analytics.router
)


@app.get("/")
def root():
    return {
        "message": "EnergyLens API running"
    }