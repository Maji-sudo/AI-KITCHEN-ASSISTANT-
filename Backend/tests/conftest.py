"""
Shared pytest fixtures for the SafeGas test suite.

All test files MUST import fixtures from here rather than duplicating
engine / session / app-override setup, otherwise the last-imported file
wins the app.dependency_overrides[get_db] slot and the others blow up
with "no such table".
"""
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.device import Device

# ── One shared in-memory engine for the whole test session ───────────────────
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── App dependency overrides (set once, at import time) ───────────────────────
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user(db: Session = Depends(get_db)):
    """Return user-1 for every authenticated endpoint during tests."""
    return db.query(User).filter(User.id == 1).first()


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

# ── Shared TestClient ─────────────────────────────────────────────────────────
client = TestClient(app)


# ── Per-test DB setup / teardown ──────────────────────────────────────────────
@pytest.fixture(autouse=True)
def setup_db():
    """
    Before each test:
      1. Drop & recreate all tables on the shared in-memory engine.
      2. Seed two users and three devices (one unpaired, two paired).

    After each test: drop all tables so state cannot bleed between tests.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db: Session = TestingSessionLocal()

    # Users
    user1 = User(id=1, name="User 1", phone="1111111111")
    user2 = User(id=2, name="User 2", phone="2222222222")
    db.add_all([user1, user2])

    # Devices
    # "dev123"       – alias used by test_safety_classification tests
    # "paired_dev_1" – alias used by test_safety_module tests (same user)
    # "unpaired_dev_1" – no user_id → must be rejected with 403
    # "paired_dev_2" – belongs to user 2
    db.add_all([
        Device(id="dev123",         name="Classification Sensor", user_id=1, status="active"),
        Device(id="paired_dev_1",   name="Kitchen Stove",         user_id=1, status="active"),
        Device(id="unpaired_dev_1", name="New Stove",             user_id=None, status="inactive"),
        Device(id="paired_dev_2",   name="Living Room",           user_id=2, status="active"),
    ])

    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)
