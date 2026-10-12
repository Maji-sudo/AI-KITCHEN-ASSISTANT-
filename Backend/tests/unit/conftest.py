"""
Unit-test conftest — sets environment variables and imports only what is
needed for pure engine tests (no FastAPI app import, no DB connection).
"""
import os

os.environ.setdefault("APP_NAME", "SafeGas AI Test")
os.environ.setdefault("APP_VERSION", "0.0.1-test")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "testsecretfortesting1234567890ab")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
