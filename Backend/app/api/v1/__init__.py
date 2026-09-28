from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.devices import router as devices_router
from app.api.v1.telemetry import router as telemetry_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.cooking import router as cooking_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.efficiency import router as efficiency_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.bookings import router as bookings_router
from app.api.v1.simulator import router as simulator_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(devices_router)
api_router.include_router(telemetry_router)
api_router.include_router(analytics_router)
api_router.include_router(cooking_router)
api_router.include_router(recommendations_router)
api_router.include_router(efficiency_router)
api_router.include_router(notifications_router)
api_router.include_router(bookings_router)
api_router.include_router(simulator_router)

