"""
SafeGas AI — Email/Password Authentication Service.

Architecture:
  Email/Password = Authentication credentials (email normalized, password bcrypt-hashed)
  SafeGas JWT    = Backend session / API authorization
  PostgreSQL     = SafeGas user database

Flow (Registration):
  1. Validate + normalize email (trim, lowercase).
  2. Reject if email already exists → HTTP 409.
  3. Hash password with bcrypt. Never store plaintext.
  4. Create User in PostgreSQL.
  5. Issue SafeGas JWT.

Flow (Login):
  1. Normalize email.
  2. Look up user by email.
  3. Verify bcrypt password hash.
  4. On mismatch: HTTP 401 (generic message, do NOT reveal whether email exists).
  5. Issue SafeGas JWT.

Security guarantees:
  - Passwords are NEVER logged, returned in responses, or stored in plaintext.
  - Login errors are generic (no oracle for email existence).
  - Email is normalized before every DB query.
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.repositories.user_repository import user_repo
from app.services.jwt_service import create_access_token
from app.schemas.auth import AuthResponse
from app.schemas.user import UserResponse
from app.core.security import hash_password, verify_password


def normalize_phone(phone_input: str) -> str:
    """
    Normalizes mobile numbers to E.164 format:
    - 10-digit Indian numbers  → +91<number>
    - 12-digit starting 91     → +<number>
    - International with +     → +<digits>
    Raises ValueError if invalid.
    """
    if not phone_input or not phone_input.strip():
        raise ValueError("Mobile number cannot be empty.")

    raw = phone_input.strip()

    if raw.startswith("+"):
        digits = "".join(c for c in raw[1:] if c.isdigit())
        if len(digits) < 7 or len(digits) > 15:
            raise ValueError("Please enter a valid mobile number with 7 to 15 digits.")
        return f"+{digits}"

    digits = "".join(c for c in raw if c.isdigit())
    if len(digits) == 10:
        return f"+91{digits}"
    elif len(digits) == 12 and digits.startswith("91"):
        return f"+{digits}"
    elif 7 <= len(digits) <= 15:
        return f"+{digits}"
    else:
        raise ValueError("Please enter a valid mobile number with 7 to 15 digits.")


class AuthService:

    # ------------------------------------------------------------------
    # REGISTER
    # ------------------------------------------------------------------
    def register_user(
        self,
        db: Session,
        name: str,
        email: str,   # already normalized by Pydantic schema
        phone: Optional[str],
        password: str,
    ) -> AuthResponse:
        """
        Register a new SafeGas user with email + password.
        Returns HTTP 409 if email already exists.
        Password is hashed with bcrypt; plaintext is never stored or logged.
        """
        # 1. Reject duplicate email
        existing = user_repo.get_by_email(db, email=email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists."
            )

        # 2. Normalize + validate phone if provided
        normalized_phone: Optional[str] = None
        if phone and phone.strip():
            try:
                normalized_phone = normalize_phone(phone)
            except ValueError as err:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(err),
                )
            # Check phone uniqueness
            phone_conflict = user_repo.get_by_phone(db, phone=normalized_phone)
            if phone_conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This phone number is already linked to another account."
                )

        # 3. Hash password — NEVER log the plaintext
        pw_hash = hash_password(password)

        # 4. Create user
        user = User(
            name=name.strip(),
            email=email,
            phone=normalized_phone,
            password_hash=pw_hash,
            language_pref="en",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"[AUTH] New user registered: id={user.id} email={user.email}")

        # 5. Issue SafeGas JWT
        token = create_access_token(user_id=user.id)
        user_resp = UserResponse.model_validate(user)

        return AuthResponse(
            access_token=token,
            token_type="bearer",
            user_id=int(user.id),
            name=str(user.name),
            email=str(user.email),
            phone=user.phone,
            is_new_user=True,
            user=user_resp,
        )

    # ------------------------------------------------------------------
    # LOGIN
    # ------------------------------------------------------------------
    def login_user(
        self,
        db: Session,
        email: str,   # already normalized by Pydantic schema
        password: str,
    ) -> AuthResponse:
        """
        Authenticate a user with email + password.
        Returns HTTP 401 for any mismatch — intentionally generic to avoid
        revealing whether the email exists (no oracle attack surface).
        """
        _INVALID_MSG = "Invalid email address or password."

        # 1. Lookup user by email
        user = user_repo.get_by_email(db, email=email)

        # 2. Verify password hash (always run verify to prevent timing attacks)
        if not user or not user.password_hash:
            # Still run a dummy verify to prevent timing oracle
            verify_password(password, "$2b$12$dummyhashtopreventtimingattacks00000000000000000000000")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=_INVALID_MSG,
            )

        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=_INVALID_MSG,
            )

        print(f"[AUTH] User authenticated: id={user.id} email={user.email}")

        # 3. Issue SafeGas JWT
        token = create_access_token(user_id=user.id)
        user_resp = UserResponse.model_validate(user)

        return AuthResponse(
            access_token=token,
            token_type="bearer",
            user_id=int(user.id),
            name=str(user.name),
            email=str(user.email),
            phone=user.phone,
            is_new_user=False,
            user=user_resp,
        )

    # ------------------------------------------------------------------
    # UPDATE PROFILE
    # ------------------------------------------------------------------
    def update_profile(
        self,
        db: Session,
        user: User,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        language_pref: Optional[str] = None,
    ) -> User:
        """
        Update name, phone, and/or language_pref for the authenticated user.
        """
        if name is not None:
            name = name.strip()
            if not name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Name cannot be empty."
                )
            user.name = name

        if phone is not None:
            try:
                normalized = normalize_phone(phone)
            except ValueError as err:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(err),
                )
            existing = user_repo.get_by_phone(db, phone=normalized)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This phone number is already linked to another account."
                )
            user.phone = normalized

        if language_pref is not None:
            user.language_pref = language_pref

        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"[AUTH] Profile updated: id={user.id}")
        return user


auth_service = AuthService()