from app.dependencies.users import get_current_user_optional
from fastapi import APIRouter, Depends, Request, Response
from app.models.users import User
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.carts import CartSchema, MessageResponseSchema
from db.dependencies import get_db
from app.services.carts import get_user_or_guest_cart
from services.carts import create_user_or_guest_cart

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
    cart = await get_user_or_guest_cart(request, user, db)

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
    total = subtotal + 5

    return {
        "id": cart.id,
        "cart_items": items,
        "subtotal": subtotal,
        "total": total,
    }


@router.post("/{beer_id}/", response_model=CartSchema)
async def add_item(
    beer_id: int,
    request: Request,
    response: Response,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_user_or_guest_cart(
        request=request, user=user, db=db, response=response
    )
    if cart is None:
        cart = create_user_or_guest_cart(
            request=request, user=user, db=db, response=response
        )
