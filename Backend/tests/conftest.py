"""
Shared pytest fixtures for the SafeGas AI test suite.
Supports both the safety module tests and the recommendation test suites.
All tests use SQLite in-memory, isolated from the real PostgreSQL database.
"""
import os
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# ── Force in-memory database and test environment ─────────────────────────────
os.environ["APP_NAME"] = "SafeGas AI Test"
os.environ["APP_VERSION"] = "0.0.1-test"
os.environ["DEBUG"] = "True"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "testsecretfortesting1234567890ab"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"

import app.models  # noqa: F401 - ensure all models are registered before create_all
from app.db.database import Base, get_db
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User
from app.models.device import Device
from app.models.recommendation import Recommendation

# ── One shared in-memory engine with StaticPool ──────────────────────────────
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TEST_ENGINE = engine
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
TestSessionLocal = TestingSessionLocal

assert "sqlite" in str(engine.url), "Safety check failed: engine is not SQLite"


# ── App dependency overrides (set once, at import time) ───────────────────────
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user(db: Session = Depends(get_db)):
    """Return user-1 for every authenticated endpoint during safety tests."""
    return db.query(User).filter(User.id == 1).first()


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

# ── Shared TestClient (imported by safety test modules) ───────────────────────
client = TestClient(app)


# ── Per-test DB setup / teardown for safety tests ─────────────────────────────
@pytest.fixture(autouse=True)
def setup_db(request):
    """
    Before each safety test:
      1. Ensure base dependency overrides are active.
      2. Drop & recreate all tables on the shared in-memory engine.
      3. Seed safety test users and devices.
    Skipped for recommendation tests in subdirectories (they manage their own tables/state).
    """
    path_str = str(request.node.fspath).replace("\\", "/")
    if any(sub in path_str for sub in ["tests/api/", "tests/integration/", "tests/unit/"]):
        yield
        return

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db: Session = TestingSessionLocal()

    # Users
    user1 = User(id=1, name="User 1", email="user1@safegas.test", phone="1111111111")
    user2 = User(id=2, name="User 2", email="user2@safegas.test", phone="2222222222")
    db.add_all([user1, user2])

    # Devices
    db.add_all([
        Device(id="dev123",         name="Classification Sensor", user_id=1, status="active"),
        Device(id="paired_dev_1",   name="Kitchen Stove",         user_id=1, status="active"),
        Device(id="unpaired_dev_1", name="New Stove",             user_id=None, status="inactive"),
        Device(id="paired_dev_2",   name="Living Room",           user_id=2, status="active"),
    ])

    db.commit()
    db.close()

    yield


# ── Recommendation suite fixtures ─────────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Ensure all tables exist for recommendation tests."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def db():
    """Provide a clean transactional session for recommendation tests."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def user(db):
    """Create a test user for recommendations."""
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
    """A second user for recommendations."""
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
    """Test device paired to user."""
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
    """Test device paired to user2."""
    d = Device(
        id="SGD-TEST-002",
        user_id=user2.id,
        name="Other Device",
        status="active",
    )
    db.add(d)
    db.flush()
    return d
