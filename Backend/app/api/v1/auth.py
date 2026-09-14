from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from google.oauth2 import id_token
from google.auth.transport import requests

from app.db.database import get_db
from app.repositories.user_repository import user_repo
from app.schemas.user import UserCreate
from app.schemas.auth import AuthResponse, OTPRequest, OTPVerify
from app.services.auth_service import auth_service

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post("/request-otp")
def request_otp(body: OTPRequest):
    """Request OTP for phone number."""
    auth_service.send_otp_for_phone(body.phone)
    return {"message": "OTP sent successfully", "phone": body.phone}


@router.post("/verify-otp", response_model=AuthResponse)
def verify_otp(body: OTPVerify, db: Session = Depends(get_db)):
    """Verify OTP and login/register user."""
    auth_resp = auth_service.verify_otp_and_login(db, body.phone, body.otp)
    if not auth_resp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    return auth_resp



# ==========================================================
# GOOGLE LOGIN
# ==========================================================

@router.post("/google", response_model=AuthResponse)
def google_login(
    google_token: str,
    db: Session = Depends(get_db)
):
    """
    Login using Google.

    The frontend sends the Google ID token.
    Backend verifies the token with Google.
    """

    try:
        # Verify Google ID token
        idinfo = id_token.verify_oauth2_token(
            google_token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        # Get Google account information
        google_id = idinfo.get("sub")
        email = idinfo.get("email")
        name = idinfo.get("name", "Google User")

        if not google_id or not email:
            raise HTTPException(
                status_code=400,
                detail="Invalid Google account information"
            )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )

    # ------------------------------------------------------
    # Find existing user
    # ------------------------------------------------------

    user = user_repo.get_by_email(
        db,
        email=email
    )

    # ------------------------------------------------------
    # Create user if first Google login
    # ------------------------------------------------------

    if not user:

        user = user_repo.create(
            db,
            obj_in=UserCreate(
                name=name,
                phone=f"google_{google_id}",
                email=email
            )
        )

    # ------------------------------------------------------
    # Create SafeGas JWT
    # ------------------------------------------------------

    token = create_access_token(
        user_id=int(user.id)
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user_id=int(user.id),
        name=str(user.name),
        phone=str(user.phone)
    )