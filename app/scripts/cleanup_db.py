import asyncio

from db.engine import AsyncSessionLocal

from app.models.users import User
from app.models.carts import Cart, CartItem
from app.models.beer import Beer, BeerEventType
from app.models.tokens import RefreshToken, PasswordResetToken, ActivationToken

from app.services.tokens import cleanup_expired_tokens


async def main() -> None:
    async with AsyncSessionLocal() as db:
        try:
            await cleanup_expired_tokens(db)
        except Exception:
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
