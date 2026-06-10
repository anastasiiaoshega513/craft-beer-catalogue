from fastapi import Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.users import User
from app.models.carts import Cart, CartItem
from app.security.guest_user import get_or_create_guest_id


async def get_user_or_guest_cart(
    request: Request, user: User | None, db: AsyncSession, response: Response
) -> Cart | None:
    stmt = select(Cart).options(
        selectinload(Cart.cart_items).selectinload(CartItem.beer)
    )

    if user:
        stmt = stmt.where(Cart.user_id == user.id)
    else:
        guest_id = get_or_create_guest_id(request=request, response=response)
        stmt = stmt.where(Cart.guest_id == guest_id)

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user_or_guest_cart(
    request: Request,
    response: Response,
    user: User | None,
    db: AsyncSession,
) -> Cart:

    if user is None:
        guest_id = get_or_create_guest_id(request=request, response=response)
        cart = Cart.create(guest_id=guest_id)
    else:
        cart = Cart.create(user_id=user.id)

    db.add(cart)
    await db.flush(cart)

    return cart
