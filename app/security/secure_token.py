"""Secure random token generation and hashing utilities."""

import hashlib
import secrets

_SECURE_TOKEN_LENGTH = 32


def generate_secure_token() -> str:
    """Generate a URL-safe random token."""
    return secrets.token_urlsafe(_SECURE_TOKEN_LENGTH)


def hash_token(token: str) -> str:
    """Return a SHA-256 hash for storing or comparing token values."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
