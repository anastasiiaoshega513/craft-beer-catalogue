from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies.users import get_current_user_optional
from app.models.beer import Beer
from app.models.carts import Cart, CartItem
from app.models.users import User
from app.schemas.carts import CartSchema
from app.services.carts import (
    create_user_or_guest_cart,
    format_cart,
    get_user_or_guest_cart,
)
from db.dependencies import get_db

router = APIRouter(
    prefix="/cart",
    tags=["Carts"],
)


@router.get("/", response_model=CartSchema)
async def get_cart(
    request: Request,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_user_or_guest_cart(request=request, user=user, db=db)

    cart = await format_cart(cart=cart)
    return cart


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
