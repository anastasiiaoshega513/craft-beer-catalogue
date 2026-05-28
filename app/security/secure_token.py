import secrets


_SECURE_TOKEN_LENGTH = 32


def generate_secure_token() -> str:
    return secrets.token_urlsafe(_SECURE_TOKEN_LENGTH)
