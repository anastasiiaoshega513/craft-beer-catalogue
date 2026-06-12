from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.users import get_current_user_optional
from app.models.beer import Beer
from app.models.carts import CartItem
from app.models.users import User
from app.schemas.carts import CartSchema
from app.services.carts import (
    format_cart,
    reload_and_format_cart,
    get_or_create_user_or_guest_cart,
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

    return await format_cart(cart)


@router.post("/{beer_id}/", response_model=CartSchema)
async def add_item(
    beer_id: int,
    request: Request,
    response: Response,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Beer).where(Beer.id == beer_id))
    beer = result.scalar_one_or_none()

    if beer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"beer_id": "Beer not found."},
        )

    if beer.total_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"beer_id": "Beer is out of stock."},
        )

    cart = await get_or_create_user_or_guest_cart(
        request=request, user=user, db=db, response=response
    )

    result = await db.execute(
        select(CartItem).where(CartItem.beer_id == beer_id, CartItem.cart_id == cart.id)
    )
    cart_item = result.scalar_one_or_none()

    if cart_item is None:
        cart_item = CartItem(beer_id=beer_id, cart_id=cart.id, amount=1)
        db.add(cart_item)
        await db.flush()

    else:
        if cart_item.amount >= beer.total_amount:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"beer_id": "Not enough beer in stock."},
            )

        cart_item.amount += 1

    await db.commit()
    return await reload_and_format_cart(cart=cart, db=db)


@router.delete("/{item_id}/", response_model=CartSchema)
async def remove_item(
    item_id: int,
    request: Request,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_user_or_guest_cart(request=request, user=user, db=db)

    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"cart_id": "Cart not found."},
        )

    result = await db.execute(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id,
        )
    )
    cart_item = result.scalar_one_or_none()

    if cart_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"item_id": "Item not found."},
        )

    cart_item.amount -= 1

    if cart_item.amount <= 0:
        await db.delete(cart_item)

    await db.commit()
    return await reload_and_format_cart(cart=cart, db=db)


@router.delete("/clear/", response_model=CartSchema)
async def remove_all_items(
    request: Request,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_user_or_guest_cart(request=request, user=user, db=db)

    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"cart_id": "Cart not found."},
        )

    for item in cart.cart_items:
        await db.delete(item)

    await db.commit()
    return await reload_and_format_cart(cart=cart, db=db)
