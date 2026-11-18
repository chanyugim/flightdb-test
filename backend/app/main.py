from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import (
    admin,
    airlines,
    airports,
    auth,
    chatbot,
    flights,
    grades,
    health,
    inquiries,
    me,
    promotions,
    reservations,
)

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
for router in (
    health.router,
    auth.router,
    chatbot.router,
    airports.router,
    airlines.router,
    grades.router,
    promotions.router,
    flights.router,
    reservations.router,
    inquiries.router,
    me.router,
    admin.router,
):
    app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {"message": settings.app_name, "version": app.version, "docs": "/docs"}
