from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from pydantic import BaseModel
from app.core.config import settings

class TokenPayload(BaseModel):
    sub: Optional[int] = None
    exp: Optional[int] = None

def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(user_id),
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        sub_val = payload.get("sub")
        return TokenPayload(
            sub=int(sub_val) if sub_val is not None else None,
            exp=payload.get("exp")
        )
    except Exception:
        return None
