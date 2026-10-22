import sys
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "SafeGas AI API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    GEMINI_API_KEY: str = ""

    GOOGLE_PLACES_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""
    GAS_AGENCY_SEARCH_RADIUS_METERS: int = 10000

    @property
    def places_api_key(self) -> str:
        return (self.GOOGLE_PLACES_API_KEY or self.GOOGLE_MAPS_API_KEY or "").strip()

    SAFEGAS_DEMO_MODE: bool = True

    API_PREFIX: str = "/api/v1"

    BACKEND_CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,https://safegas-ai.vercel.app,https://ai-kitchen-assitant.vercel.app"
    )

    BACKEND_CORS_ORIGIN_REGEX: str | None = (
        r"^https:\/\/(safegas-ai.*\.vercel\.app|.*\.vercel\.app)$"
    )

    @property
    def cors_origin_regex(self) -> str | None:
        if self.BACKEND_CORS_ORIGIN_REGEX:
            trimmed = self.BACKEND_CORS_ORIGIN_REGEX.strip()
            return trimmed if trimmed else None
        return None

    @property
    def cors_origins(self) -> list[str]:
        raw = (self.BACKEND_CORS_ORIGINS or "").strip()

        # In production (DEBUG=False):
        if not self.DEBUG:
            if "*" in [o.strip() for o in raw.split(",")]:
                raise ValueError(
                    "Security violation: Wildcard CORS origin '*' is strictly prohibited in production (DEBUG=False). "
                    "Configure explicit frontend domains in BACKEND_CORS_ORIGINS."
                )
            if not raw:
                raise ValueError(
                    "Configuration error: BACKEND_CORS_ORIGINS must be set in production to the deployed frontend domain."
                )
            # In production, only return explicitly configured origins (no automatic localhost)
            return [
                origin.strip().rstrip("/")
                for origin in raw.split(",")
                if origin.strip()
            ]

        # In development / testing (DEBUG=True):
        default_dev = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
        if raw == "*":
            return ["*"]
        configured = [
            origin.strip().rstrip("/")
            for origin in raw.split(",")
            if origin.strip()
        ]
        return list(dict.fromkeys(default_dev + configured))

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

try:
    settings = Settings()
except ValidationError as exc:
    missing = [
        str(err["loc"][0])
        for err in exc.errors()
        if err.get("type") == "missing"
    ]
    if missing:
        print(
            f"\n======================================================================\n"
            f"[SafeGas AI Startup Error] Missing required environment variable(s):\n"
            f"  -> {', '.join(missing)}\n\n"
            f"Please configure them in your Render Dashboard / deployment environment:\n"
            f"  - DATABASE_URL: PostgreSQL connection string\n"
            f"  - JWT_SECRET: Minimum 32-character secret key for JWT signing\n"
            f"======================================================================\n",
            file=sys.stderr,
            flush=True,
        )
    raise