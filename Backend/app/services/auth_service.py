"""
Development OTP Service.

For development/testing:
OTP is always 123456.

Do NOT use this implementation in production.
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.jwt_service import create_access_token
from app.schemas.auth import AuthResponse

OTP_CODE = "123456"


def send_otp(phone: str) -> None:
    """
    Development-only OTP sender.
    """
    print(f"[DEV OTP] Phone: {phone}")
    print(f"[DEV OTP] OTP: {OTP_CODE}")


def verify_otp(phone: str, otp: str) -> bool:
    """
    Verify the development OTP.
    """
    return otp == OTP_CODE

class AuthService:
    def send_otp_for_phone(self, phone: str) -> None:
        send_otp(phone)

    def verify_otp_and_login(self, db: Session, phone: str, otp: str) -> Optional[AuthResponse]:
        if not verify_otp(phone, otp):
            return None
        
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            user = User(name="User", phone=phone)
            db.add(user)
            db.commit()
            db.refresh(user)
            
        token = create_access_token(user_id=user.id)
        return AuthResponse(
            access_token=token,
            token_type="bearer",
            user={"id": user.id, "name": user.name, "phone": user.phone}
        )

auth_service = AuthService()