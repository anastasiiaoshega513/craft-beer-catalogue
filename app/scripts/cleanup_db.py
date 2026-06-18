"""Database cleanup script for expired tokens and unactivated user accounts."""

import asyncio

from app.models.beer import Beer, BeerEventType
from app.models.carts import Cart, CartItem
from app.models.tokens import ActivationToken, PasswordResetToken, RefreshToken
from app.models.users import User
from app.services.tokens import cleanup_expired_tokens
from db.engine import AsyncSessionLocal


async def main() -> None:
    async with AsyncSessionLocal() as db:
        try:
            await cleanup_expired_tokens(db)
        except Exception:
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
