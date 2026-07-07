"""Cart lookup, creation, and response formatting shared by cart routes.

Authenticated users are matched by user_id, while guests are matched by the guest_id
cookie. Read-only cart lookup does not create a cookie or a cart; creation happens
only when a cart is needed for a write operation.
"""

from fastapi import HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.carts import Cart, CartItem
from app.models.users import User
from app.security.guest_user import GUEST_COOKIE, get_or_create_guest_id


async def get_user_or_guest_cart(request: Request, user: User | None, db: AsyncSession) -> Cart | None:
    """
    Return an existing cart for an authenticated user or guest.

    This function is read-only. For guests without a guest_id cookie, it returns
    None instead of creating a cookie or a new cart.
    """
    stmt = select(Cart).options(selectinload(Cart.cart_items).selectinload(CartItem.beer))

    if user:
        stmt = stmt.where(Cart.user_id == user.id)
    else:
        guest_id = request.cookies.get(GUEST_COOKIE)

        if guest_id is None:
            return None

        stmt = stmt.where(Cart.guest_id == guest_id)

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_or_create_user_or_guest_cart(
    request: Request,
    response: Response,
    user: User | None,
    db: AsyncSession,
) -> Cart:
    """
    Return an existing cart or create one for an authenticated user or guest.

    For guests, a guest_id cookie is created when it does not already exist.
    """
    stmt = select(Cart)

    if user is None:
        guest_id = get_or_create_guest_id(request=request, response=response)
        result = await db.execute(stmt.where(Cart.guest_id == guest_id))
        cart = result.scalar_one_or_none()

        if cart is None:
            cart = Cart(guest_id=guest_id)
            db.add(cart)
            await db.flush()
    else:
        result = await db.execute(stmt.where(Cart.user_id == user.id))
        cart = result.scalar_one_or_none()

        if cart is None:
            cart = Cart(user_id=user.id)
            db.add(cart)
            await db.flush()

    return cart


async def format_cart(cart: Cart | None) -> dict:
    """
    Build the cart response returned by the API.

    Returns an empty cart response when the cart does not exist. Cart items with
    non-positive amounts are ignored. The delivery fee is added only when the
    cart contains valid items.
    """
    if cart is None:
        return {
            "id": None,
            "cart_items": [],
            "subtotal": 0,
            "total": 0,
        }

    items = []

    for item in cart.cart_items:

        if item.amount <= 0:
            continue

        items.append(
            {
                "id": item.id,
                "beer_id": item.beer.id,
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


async def reload_and_format_cart(cart: Cart, db: AsyncSession) -> dict:
    """
    Reload a cart from the database and return its formatted response.

    Used after cart changes to avoid formatting stale relationship data from the
    current SQLAlchemy session.
    """
    result = await db.execute(
        select(Cart)
        .options(selectinload(Cart.cart_items).selectinload(CartItem.beer))
        .where(Cart.id == cart.id)
        .execution_options(populate_existing=True)
    )

    fresh_cart = result.scalar_one_or_none()

    return await format_cart(fresh_cart)


async def get_cart_or_404(
    request: Request,
    user: User | None,
    db: AsyncSession,
):
    cart = await get_user_or_guest_cart(request=request, user=user, db=db)

    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"cart_id": "Cart not found."},
        )

    return cart


async def get_cart_item_or_404(
    item_id: int,
    cart_id: int,
    db: AsyncSession,
    load_beer: bool = False,
):
    query = select(CartItem).where(
        CartItem.id == item_id,
        CartItem.cart_id == cart_id,
    )

    if load_beer:
        query = query.options(selectinload(CartItem.beer))

    result = await db.execute(query)
    cart_item = result.scalar_one_or_none()

    if cart_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"item_id": "Item not found."},
        )

    return cart_item
