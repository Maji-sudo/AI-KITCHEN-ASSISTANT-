"""
Password hashing and verification using bcrypt.
Passwords are NEVER stored in plaintext, logged, or returned in API responses.
"""
import bcrypt


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    # Truncate password to 72 bytes if needed (bcrypt 72-byte max)
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False
