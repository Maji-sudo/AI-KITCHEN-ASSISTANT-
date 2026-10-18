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

    SAFEGAS_DEMO_MODE: bool = True

    API_PREFIX: str = "/api/v1"

    BACKEND_CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    )

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

settings = Settings()