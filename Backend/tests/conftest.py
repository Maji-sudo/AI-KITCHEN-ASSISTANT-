"""
conftest.py — shared fixtures for API and integration recommendation tests.

Uses SQLite (in-memory) so tests never touch the real PostgreSQL database.
The app's DATABASE_URL is overridden before any model import.
"""
import os
import pytest

# ── Override settings before app modules are imported ────────────────────────
os.environ.setdefault("APP_NAME", "SafeGas AI Test")
os.environ.setdefault("APP_VERSION", "0.0.1-test")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "testsecretfortesting1234567890ab")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.database import Base
from app.main import app
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.device import Device
from app.models.recommendation import Recommendation

# ── In-memory SQLite engine shared across all tests ───────────────────────────
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once per test session."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture()
def db():
    """Provide a clean transactional session per test (rolled back after)."""
    connection = TEST_ENGINE.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def user(db):
    """Create a test user."""
    u = User(
        name="Test User",
        email="test@safegas.ai",
        password_hash="$2b$12$fakehashfortesting",
        language_pref="en",
    )
    db.add(u)
    db.flush()
    return u


@pytest.fixture()
def user2(db):
    """A second user — used to test cross-user access."""
    u = User(
        name="Other User",
        email="other@safegas.ai",
        password_hash="$2b$12$fakehashfortesting",
        language_pref="en",
    )
    db.add(u)
    db.flush()
    return u


@pytest.fixture()
def device(db, user):
    """Create a test device paired to user."""
    d = Device(
        id="SGD-TEST-001",
        user_id=user.id,
        name="Test Device",
        status="active",
    )
    db.add(d)
    db.flush()
    return d


@pytest.fixture()
def device2(db, user2):
    """A device belonging to user2."""
    d = Device(
        id="SGD-TEST-002",
        user_id=user2.id,
        name="Other Device",
        status="active",
    )
    db.add(d)
    db.flush()
    return d


def make_token(user_id: int) -> str:
    from app.services.jwt_service import create_access_token
    return create_access_token(user_id)


@pytest.fixture()
def client(db, user, device):
    """TestClient with DB and auth overrides for user (owner of device)."""
    def override_db():
        yield db

    def override_auth():
        return user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def client_user2(db, user2, device2):
    """TestClient authenticated as user2."""
    def override_db():
        yield db

    def override_auth():
        return user2

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def unauthenticated_client(db):
    """TestClient with DB override but NO auth override."""
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    # intentionally do NOT override get_current_user
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
