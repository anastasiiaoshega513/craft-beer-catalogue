"""Cleanup helpers for expired tokens and stale unactivated accounts."""

from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tokens import ActivationToken, PasswordResetToken, RefreshToken
from app.models.users import User
from app.services.users import utc_now_naive


async def cleanup_expired_auth_records(db: AsyncSession) -> None:
    """
    Delete expired authentication tokens and stale unactivated users.

    Refresh and password reset tokens are removed as soon as they expire.
    Unactivated users are removed only after their activation token has been
    expired for more than one day.
    """
    now = utc_now_naive()
    unactivated_user_cutoff = now - timedelta(days=1)

    await db.execute(delete(RefreshToken).where(RefreshToken.expires_at < now))
    await db.execute(
        delete(PasswordResetToken).where(PasswordResetToken.expires_at < now)
    )

    result = await db.execute(
        select(User)
        .join(ActivationToken)
        .where(
            User.is_active.is_(False),
            ActivationToken.expires_at < unactivated_user_cutoff,
        )
    )

    old_unactivated_users = result.scalars().all()

    for user in old_unactivated_users:
        await db.delete(user)

    await db.commit()
