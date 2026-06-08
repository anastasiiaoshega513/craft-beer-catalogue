from dependencies.users import get_current_user_optional
from fastapi import APIRouter, Depends, Request
from models.carts import Cart, CartItem
from models.users import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.schemas.carts import CartSchema, MessageResponseSchema
from db.dependencies import get_db

router = APIRouter(
    prefix="/cart",
    tags=["Carts"],
)


@router.get("/", response_model=CartSchema | MessageResponseSchema)
async def get_cart(
    request: Request,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    if user:
        stmt = (
            select(Cart)
            .options(selectinload(Cart.cart_items).selectinload(CartItem.beer))
            .where(Cart.user_id == user.id)
        )
    else:
        guest_id = request.cookies["guest_id"]
        stmt = (
            select(Cart)
            .options(selectinload(Cart.cart_items).selectinload(CartItem.beer))
            .where(Cart.guest_id == guest_id)
        )

    result = await db.execute(stmt)
    cart = result.scalar_one_or_none()

    if cart is None:
        return {
            "id": None,
            "cart_items": [],
            "subtotal": 0,
            "total": 0,
        }

    items = []

    for item in cart.cart_items:
        beer = item.beer

        items.append(
            {
                "id": item.id,
                "name": beer.name,
                "quantity": item.amount,
                "price": beer.price,
                "image_url": beer.image_url,
            }
        )

    subtotal = sum(item["price"] * item["quantity"] for item in items)
    total = subtotal + 5

    return {
        "id": cart.id,
        "cart_items": items,
        "subtotal": subtotal,
        "total": total,
    }


@router.post("/{item_id}", response_model=CartSchema)
async def add_item():
    pass
