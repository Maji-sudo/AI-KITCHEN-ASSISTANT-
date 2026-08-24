"""
Shared FastAPI dependencies used across all routers.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.jwt_service import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/verify-otp")

# Demo user singleton — used when frontend sends the demo-token
_DEMO_USER = None

def _get_demo_user(db: Session) -> User:
    """Return the first user in the DB as demo, or a synthetic User object."""
    global _DEMO_USER
    if _DEMO_USER is None:
        db_user = db.query(User).first()
        if db_user:
            _DEMO_USER = db_user
        else:
            # Create a fully synthetic in-memory User (not saved to DB)
            demo = User()
            demo.id = 0
            demo.name = "Demo User"
            demo.phone = "9999999999"
            _DEMO_USER = demo
    return _DEMO_USER


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decode JWT and return the authenticated User. Raises 401 if invalid.
    Special case: 'demo-token' is accepted for frontend demo mode."""

    # ── Demo mode bypass ───────────────────────────────────────────────────
    if token == "demo-token":
        return _get_demo_user(db)
    # ──────────────────────────────────────────────────────────────────────

    payload = decode_access_token(token)
    if payload is None or payload.sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == payload.sub).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
