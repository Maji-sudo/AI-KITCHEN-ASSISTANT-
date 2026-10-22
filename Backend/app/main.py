from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from sqlalchemy import text
from app.db.database import engine
from app.api.v1 import api_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Powered Smart Kitchen Backend"
)

# CORS middleware for frontend communication
cors_origins = settings.cors_origins
cors_origin_regex = settings.cors_origin_regex
allow_credentials = False if "*" in cors_origins else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "*",
    ],
)

from app.api.v1.gas_agencies import router as gas_agencies_router

app.include_router(api_router, prefix="/api/v1")
# Backward-compatible direct alias for /api/gas-agencies/nearby
app.include_router(gas_agencies_router, prefix="/api")

@app.get("/")
def root():
    return {
        "message": "SafeGas AI Backend Running"
    }

@app.get("/config")
def config():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG
    }
@app.get("/db-check")
def db_check():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.scalar()

    return {
        "database": "Connected",
        "version": version
    }