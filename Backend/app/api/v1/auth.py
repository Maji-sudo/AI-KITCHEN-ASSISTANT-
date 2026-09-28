from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_user
from app.schemas.user import UserResponse, UpdateProfileRequest
from app.schemas.auth import AuthResponse, RegisterRequest, LoginRequest
from app.services.auth_service import auth_service
from app.models.user import User

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


# ==========================================================
# REGISTER — POST /api/v1/auth/register
# ==========================================================

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user with name, email, phone (optional), and password.
    Returns HTTP 409 if email already exists.
    Returns HTTP 201 + JWT on success.
    """
    return auth_service.register_user(
        db=db,
        name=body.name,
        email=body.email,      # normalized by Pydantic schema
        phone=body.phone,
        password=body.password,
    )


# ==========================================================
# LOGIN — POST /api/v1/auth/login
# ==========================================================

@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with email + password.
    Returns HTTP 401 for invalid credentials (generic message, no oracle).
    Returns JWT on success.
    """
    return auth_service.login_user(
        db=db,
        email=body.email,      # normalized by Pydantic schema
        password=body.password,
    )


# ==========================================================
# GET CURRENT USER — GET /api/v1/auth/me
# ==========================================================

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user


# ==========================================================
# UPDATE PROFILE — PATCH /api/v1/auth/me
# ==========================================================

@router.patch("/me", response_model=UserResponse)
def update_profile(
    body: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the authenticated user's profile fields:
    - name, phone, language_pref
    All fields are optional; only provided fields are updated.
    """
    return auth_service.update_profile(
        db=db,
        user=current_user,
        name=body.name,
        phone=body.phone,
        language_pref=body.language_pref,
    )