from typing import Optional
from pydantic import BaseModel

# --- OTP Request / Verify ---
class OTPRequest(BaseModel):
    phone: str

class OTPVerify(BaseModel):
    phone: str
    otp: str

# --- Token Response ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[int] = None  # user_id

# --- Auth Response (returned on successful login) ---
class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    phone: str
