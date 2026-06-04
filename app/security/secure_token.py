import hashlib
import secrets

_SECURE_TOKEN_LENGTH = 32


def generate_secure_token() -> str:
    return secrets.token_urlsafe(_SECURE_TOKEN_LENGTH)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
