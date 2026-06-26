"""User route helpers for common lookups, auth errors, and datetime handling."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Return a user by normalized email address."""
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


def invalid_refresh_token_exception() -> HTTPException:
    """Build a 401 error for missing, invalid, or expired refresh tokens."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"refresh_token": "Invalid or expired refresh token."},
    )


def invalid_reset_token_exception() -> HTTPException:
    """Build a 400 error for invalid or expired password reset tokens."""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"reset_token": "Invalid email or token."},
    )


def internal_server_error(message: str) -> HTTPException:
    """Build a 500 error response with a server_error detail message."""
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"server_error": message},
    )
