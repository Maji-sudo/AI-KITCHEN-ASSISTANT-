"""
Tests for deployment configuration, CORS validation, and environment error handling.
"""
import os
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app


def test_root_health_check_without_db():
    """Verify GET / returns 200 and health message without hitting the database."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "SafeGas AI Backend Running"}


def test_config_endpoint():
    """Verify GET /config returns application metadata."""
    client = TestClient(app)
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "version" in data
    assert "debug" in data


def test_missing_database_url_raises_validation_error(monkeypatch):
    """Verify Settings raises ValidationError if DATABASE_URL is missing."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            JWT_SECRET="any_secret_key_at_least_32_characters",
            _env_file=None,
        )
    errors = exc_info.value.errors()
    missing_fields = [e["loc"][0] for e in errors if e.get("type") == "missing"]
    assert "DATABASE_URL" in missing_fields


def test_missing_jwt_secret_raises_validation_error(monkeypatch):
    """Verify Settings raises ValidationError if JWT_SECRET is missing."""
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            DATABASE_URL="sqlite:///:memory:",
            _env_file=None,
        )
    errors = exc_info.value.errors()
    missing_fields = [e["loc"][0] for e in errors if e.get("type") == "missing"]
    assert "JWT_SECRET" in missing_fields


def test_production_cors_rejects_wildcard():
    """In production (DEBUG=False), wildcard CORS '*' must raise ValueError."""
    s = Settings(
        DEBUG=False,
        DATABASE_URL="sqlite:///:memory:",
        JWT_SECRET="production_secret_32_chars_minimum_value",
        BACKEND_CORS_ORIGINS="*",
        _env_file=None,
    )
    with pytest.raises(ValueError, match="Wildcard CORS origin"):
        _ = s.cors_origins


def test_production_cors_rejects_empty():
    """In production (DEBUG=False), empty BACKEND_CORS_ORIGINS must raise ValueError."""
    s = Settings(
        DEBUG=False,
        DATABASE_URL="sqlite:///:memory:",
        JWT_SECRET="production_secret_32_chars_minimum_value",
        BACKEND_CORS_ORIGINS="",
        _env_file=None,
    )
    with pytest.raises(ValueError, match="BACKEND_CORS_ORIGINS must be set"):
        _ = s.cors_origins


def test_production_cors_parses_explicit_origins():
    """In production (DEBUG=False), explicit origins are parsed and stripped of trailing slashes."""
    s = Settings(
        DEBUG=False,
        DATABASE_URL="sqlite:///:memory:",
        JWT_SECRET="production_secret_32_chars_minimum_value",
        BACKEND_CORS_ORIGINS="https://safegas-ai.vercel.app/, https://custom-domain.com",
        _env_file=None,
    )
    assert s.cors_origins == [
        "https://safegas-ai.vercel.app",
        "https://custom-domain.com",
    ]


def test_development_cors_allows_localhost_and_wildcard():
    """In development (DEBUG=True), localhost origins are preserved and wildcard is accepted."""
    s = Settings(
        DEBUG=True,
        DATABASE_URL="sqlite:///:memory:",
        JWT_SECRET="dev_secret_32_chars_minimum_value",
        BACKEND_CORS_ORIGINS="*",
        _env_file=None,
    )
    assert s.cors_origins == ["*"]


def test_cors_preflight_production_vercel_origin():
    """Verify preflight OPTIONS request from production Vercel origin succeeds with 200 and required CORS headers."""
    client = TestClient(app)
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://safegas-ai.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://safegas-ai.vercel.app"
    methods = response.headers.get("access-control-allow-methods", "")
    assert "POST" in methods
    assert "OPTIONS" in methods
    allow_headers = response.headers.get("access-control-allow-headers", "").lower()
    assert "authorization" in allow_headers
    assert "content-type" in allow_headers


def test_cors_preflight_vercel_preview_origin():
    """Verify preflight OPTIONS request from a Vercel preview deployment URL matches regex and succeeds."""
    client = TestClient(app)
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://safegas-ai-git-fix-cors-team.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://safegas-ai-git-fix-cors-team.vercel.app"


def test_cors_preflight_disallowed_origin():
    """Verify preflight OPTIONS request from an untrusted origin is rejected with 400."""
    client = TestClient(app)
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://malicious-site.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers

