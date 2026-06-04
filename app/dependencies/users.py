from fastapi import Depends, Request, HTTPException, status
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app import config
from db.dependencies import get_db
from app.security.jwt_token import (
    JWTAuthManager,
    get_token,
    TokenExpiredError,
    InvalidTokenError,
)
from app.models.users import User

jwt_manager = JWTAuthManager(
    secret_key_access=config.JWT_ACCESS_SECRET_KEY,
    secret_key_refresh=config.JWT_REFRESH_SECRET_KEY,
)


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    token = get_token(request)

    try:
        payload = jwt_manager.decode_access_token(token)
        user_id = int(payload["sub"])
    except (TokenExpiredError, InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not activated.",
        )

    return user
