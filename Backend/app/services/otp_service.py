"""
OTP Service — generates, stores, and verifies one-time passwords.

In development, OTPs are printed to the console and stored in an in-memory
dict (keyed by phone number). In production, replace the _send_otp() method
with a real SMS gateway (e.g., Twilio, MSG91).
"""
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Tuple
from app.core.config import settings

# In-memory store: { phone: (otp_code, expiry_datetime) }
_otp_store: Dict[str, Tuple[str, datetime]] = {}


def _generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def _send_otp(phone: str, otp: str) -> None:
    """
    TODO: Replace with a real SMS gateway in production.
    For now, just prints to console (visible in uvicorn logs).
    """
    print(f"[OTP SERVICE] Phone: {phone}  OTP: {otp}")


def send_otp(phone: str) -> None:
    """Generate a fresh OTP, store it, and dispatch it to the user's phone."""
    otp = _generate_otp()
    expiry = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    _otp_store[phone] = (otp, expiry)
    _send_otp(phone, otp)


def verify_otp(phone: str, otp: str) -> bool:
    """
    Returns True if the OTP matches and has not expired.
    In DEBUG mode, 123456 is also accepted.
    """
    if settings.DEBUG and otp == "123456":
        return True

    entry = _otp_store.get(phone)
    if not entry:
        return False
    stored_otp, expiry = entry
    if datetime.utcnow() > expiry:
        _otp_store.pop(phone, None)
        return False
    if stored_otp != otp:
        return False
    # Consume the OTP
    _otp_store.pop(phone, None)
    return True
