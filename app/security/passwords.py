"""Password hashing and verification helpers."""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12, deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash for a raw password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a raw password against a stored password hash."""
    return pwd_context.verify(plain_password, hashed_password)
