"""Cleanup helpers for expired tokens and stale unactivated accounts."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tokens import ActivationToken, PasswordResetToken, RefreshToken
from app.models.users import User


async def cleanup_expired_tokens(db: AsyncSession) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    yesterday = now - timedelta(days=1)

    await db.execute(delete(RefreshToken).where(RefreshToken.expires_at < now))
    await db.execute(
        delete(PasswordResetToken).where(PasswordResetToken.expires_at < now)
    )

    result = await db.execute(
        select(User)
        .join(ActivationToken)
        .where(
            User.is_active.is_(False),
            ActivationToken.expires_at < yesterday,
        )
    )

    old_unactivated_users = result.scalars().all()

    for user in old_unactivated_users:
        await db.delete(user)

    await db.commit()
