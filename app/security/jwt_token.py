"""JWT access and refresh token creation and validation utilities."""

from datetime import datetime, timedelta, timezone

from jose import ExpiredSignatureError, JWTError, jwt


class TokenExpiredError(Exception):
    """Raised when a JWT has expired."""

    pass


class InvalidTokenError(Exception):
    """Raised when a JWT is invalid or cannot be decoded."""

    pass


class JWTAuthManager:
    """Create and decode JWT access and refresh tokens."""

    _ALGORITHM = "HS256"
    _ACCESS_TOKEN_EXPIRE_MINUTES = 60
    _REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

    def __init__(self, secret_key_access: str, secret_key_refresh: str) -> None:
        self._secret_key_access = secret_key_access
        self._secret_key_refresh = secret_key_refresh

    def _create_token(
        self, data: dict, secret_key: str, expires_delta: timedelta
    ) -> str:
        """Create a signed JWT with an expiration claim."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, secret_key, algorithm=self._ALGORITHM)

    def create_access_token(self, data: dict) -> str:
        """Create a short-lived access token."""
        return self._create_token(
            data,
            self._secret_key_access,
            timedelta(minutes=self._ACCESS_TOKEN_EXPIRE_MINUTES),
        )

    def create_refresh_token(self, data: dict) -> str:
        """Create a refresh token used to request new access tokens."""
        return self._create_token(
            data,
            self._secret_key_refresh,
            timedelta(minutes=self._REFRESH_TOKEN_EXPIRE_MINUTES),
        )

    def decode_access_token(self, token: str) -> dict:
        """Decode and validate an access token."""
        try:
            return jwt.decode(
                token, self._secret_key_access, algorithms=[self._ALGORITHM]
            )
        except ExpiredSignatureError:
            raise TokenExpiredError()
        except JWTError:
            raise InvalidTokenError()

    def decode_refresh_token(self, token: str) -> dict:
        """Decode and validate a refresh token."""
        try:
            return jwt.decode(
                token, self._secret_key_refresh, algorithms=[self._ALGORITHM]
            )
        except ExpiredSignatureError:
            raise TokenExpiredError()
        except JWTError:
            raise InvalidTokenError()
