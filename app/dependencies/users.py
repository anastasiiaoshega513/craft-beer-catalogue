from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import config
from app.models.users import User
from app.security.jwt_token import InvalidTokenError, JWTAuthManager, TokenExpiredError
from db.dependencies import get_db

jwt_manager = JWTAuthManager(
    secret_key_access=config.JWT_ACCESS_SECRET_KEY,
    secret_key_refresh=config.JWT_REFRESH_SECRET_KEY,
)

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:

    token = credentials.credentials

    try:
        payload = jwt_manager.decode_access_token(token)
        user_id = int(payload["sub"])
    except (TokenExpiredError, InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"access_token": ["Invalid or expired access token."]},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"access_token": ["Invalid access token."]},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"user_account": ["User account is not activated."]},
        )

    return user
