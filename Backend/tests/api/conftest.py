"""
Recommendation API test fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user, get_db


@pytest.fixture()
def client(db, user, device):
    """TestClient with DB and auth overrides for user (owner of device)."""
    def override_db():
        yield db

    def override_auth():
        return user

    saved_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_auth
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved_overrides)


@pytest.fixture()
def client_user2(db, user2, device2):
    """TestClient authenticated as user2."""
    def override_db():
        yield db

    def override_auth():
        return user2

    saved_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_auth
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved_overrides)


@pytest.fixture()
def unauthenticated_client(db):
    """TestClient with DB override but NO auth override."""
    def override_db():
        yield db

    saved_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides.pop(get_current_user, None)
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved_overrides)
