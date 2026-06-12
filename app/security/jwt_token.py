from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, status
from jose import ExpiredSignatureError, JWTError, jwt


class TokenExpiredError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


def get_token(request: Request) -> str:

    authorization: str | None = request.headers.get("Authorization")

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"authorization": "Authorization header is missing"},
        )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "authorization": "Invalid Authorization header format. Expected 'Bearer <token>'"
            },
        )

    return token


class JWTAuthManager:

    _ALGORITHM = "HS256"
    _ACCESS_TOKEN_EXPIRE_MINUTES = 60
    _REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

    def __init__(self, secret_key_access: str, secret_key_refresh: str) -> None:
        self._secret_key_access = secret_key_access
        self._secret_key_refresh = secret_key_refresh

    def _create_token(
        self, data: dict, secret_key: str, expires_delta: timedelta
    ) -> str:

        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, secret_key, algorithm=self._ALGORITHM)

    def create_access_token(self, data: dict) -> str:

        return self._create_token(
            data,
            self._secret_key_access,
            timedelta(minutes=self._ACCESS_TOKEN_EXPIRE_MINUTES),
        )

    def create_refresh_token(self, data: dict) -> str:

        return self._create_token(
            data,
            self._secret_key_refresh,
            timedelta(minutes=self._REFRESH_TOKEN_EXPIRE_MINUTES),
        )

    def decode_access_token(self, token: str) -> dict:

        try:
            return jwt.decode(
                token, self._secret_key_access, algorithms=[self._ALGORITHM]
            )
        except ExpiredSignatureError:
            raise TokenExpiredError
        except JWTError:
            raise InvalidTokenError

    def decode_refresh_token(self, token: str) -> dict:

        try:
            return jwt.decode(
                token, self._secret_key_refresh, algorithms=[self._ALGORITHM]
            )
        except ExpiredSignatureError:
            raise TokenExpiredError
        except JWTError:
            raise InvalidTokenError
