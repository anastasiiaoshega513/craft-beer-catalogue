from fastapi import Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.carts import Cart, CartItem
from app.models.users import User
from app.security.guest_user import get_or_create_guest_id, GUEST_COOKIE


async def get_user_or_guest_cart(
    request: Request, user: User | None, db: AsyncSession
) -> Cart | None:
    stmt = select(Cart).options(
        selectinload(Cart.cart_items).selectinload(CartItem.beer)
    )

    if user:
        stmt = stmt.where(Cart.user_id == user.id)
    else:
        guest_id = request.cookies.get(GUEST_COOKIE)

        if guest_id is None:
            return None

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
    await db.flush()

    return cart


async def format_cart(cart: Cart | None) -> dict:
    if cart is None:
        return {
            "id": None,
            "cart_items": [],
            "subtotal": 0,
            "total": 0,
        }

    items = []

    for item in cart.cart_items:
        items.append(
            {
                "id": item.id,
                "name": item.beer.name,
                "quantity": item.amount,
                "price": item.beer.price,
                "image_url": item.beer.image_url,
            }
        )

    subtotal = sum(item["price"] * item["quantity"] for item in items)

    delivery_fee = 5 if items else 0
    total = subtotal + delivery_fee

    return {
        "id": cart.id,
        "cart_items": items,
        "subtotal": subtotal,
        "total": total,
    }
