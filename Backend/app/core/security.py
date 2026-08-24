# Security helpers for auth, JWT tokens, and hashing

def hash_password(password: str) -> str:
    # Placeholder for hashing logic (e.g. passlib/bcrypt)
    return f"hashed_{password}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashed_password == f"hashed_{plain_password}"
