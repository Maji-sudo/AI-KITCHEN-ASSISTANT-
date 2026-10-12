import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import asyncio

from app.main import app
from app.db.database import get_db, Base
from app.api.deps import get_current_user
from app.services.realtime_service import realtime_manager
from app.models.device import Device
from app.models.user import User

# --- Fixtures ---

@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()

@pytest.fixture
def test_user(test_db: Session):
    user = User(id=1, email="demo@safegas.com", name="Demo User", phone="+1234567890", language_pref="en")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def second_user(test_db: Session):
    user = User(id=2, email="user2@safegas.com", name="User Two", phone="+0987654321", language_pref="en")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def test_device(test_db: Session, test_user: User):
    device = Device(id="phase5_device", user_id=test_user.id, name="Test Stove")
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    return device

@pytest.fixture
def test_client(test_db: Session, test_user: User):
    def override_get_db():
        yield test_db

    def override_get_current_user():
        return test_user

    original_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)

@pytest.fixture
def normal_user_token_headers():
    from app.services.jwt_service import create_access_token
    token = create_access_token(user_id=1)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def second_user_token_headers():
    from app.services.jwt_service import create_access_token
    token = create_access_token(user_id=2)
    return {"Authorization": f"Bearer {token}"}

def test_realtime_connection_auth_failure(test_client: TestClient, test_db: Session, test_device: Device):
    """Test that SSE stream requires valid authentication."""
    response = test_client.get(f"/api/v1/devices/{test_device.id}/safety/stream")
    assert response.status_code == 422  # Missing query param

    response = test_client.get(f"/api/v1/devices/{test_device.id}/safety/stream?token=invalid")
    assert response.status_code == 401

def test_realtime_connection_unauthorized_device(
    test_client: TestClient, test_db: Session, test_device: Device, second_user_token_headers: dict
):
    """Test that User B cannot subscribe to User A's device."""
    # extract token from headers
    token = second_user_token_headers["Authorization"].split(" ")[1]
    
    response = test_client.get(f"/api/v1/devices/{test_device.id}/safety/stream?token={token}")
    assert response.status_code == 403

import asyncio
from httpx import AsyncClient

def test_realtime_event_delivery(test_device: Device, normal_user_token_headers: dict):
    """Test that a safety update is routed through the manager."""
    # Run the event routing logic in an isolated event loop for testing
    async def run_test():
        queue = await realtime_manager.subscribe(test_device.id)
        assert len(realtime_manager.active_connections[test_device.id]) == 1
        
        payload = {"type": "SAFETY_UPDATE", "data": {"status": "critical"}}
        realtime_manager.publish_safety_update(test_device.id, payload)
        
        received = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert received == payload
        
        realtime_manager.unsubscribe(test_device.id, queue)
        assert test_device.id not in realtime_manager.active_connections

    asyncio.run(run_test())
