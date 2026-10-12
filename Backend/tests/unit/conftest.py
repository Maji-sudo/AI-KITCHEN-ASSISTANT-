"""
Unit-test conftest — sets environment variables and imports only what is
needed for pure engine tests (no FastAPI app import, no DB connection).
"""
import os

os.environ["APP_NAME"] = "SafeGas AI Test"
os.environ["APP_VERSION"] = "0.0.1-test"
os.environ["DEBUG"] = "True"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "testsecretfortesting1234567890ab"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
