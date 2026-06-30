from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies.users import get_current_user_optional
from app.models.beer import Beer
from app.models.carts import CartItem
from app.models.users import User
from app.schemas.carts import CartSchema
from app.services.carts import (
    format_cart,
    get_or_create_user_or_guest_cart,
    get_user_or_guest_cart,
    reload_and_format_cart, get_cart_or_404,
)
from db.dependencies import get_db

router = APIRouter(
    prefix="/cart",
    tags=["Carts"],
)


@router.get(
    "/",
    response_model=CartSchema,
    summary="Get cart",
    description=(
        "Return the current authenticated or guest cart. "
        "Does not create a cart or guest cookie if they do not already exist."
    ),
)
async def get_cart(
    request: Request,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_user_or_guest_cart(request=request, user=user, db=db)

    return await format_cart(cart)


@router.post(
    "/{beer_id}/",
    response_model=CartSchema,
    summary="Add beer to cart",
    description=(
        "Add one or more beers to the current cart. Creates a guest cart and guest_id "
        "cookie when the user is not authenticated and no guest cart exists."
    ),
    responses={
        404: {"description": "Beer not found."},
        409: {"description": "Beer is out of stock or requested amount exceeds stock."},
    },
)
async def add_cart_item(
    beer_id: int,
    request: Request,
    response: Response,
    quantity: int = Query(1, ge=1),
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Add one or more beers to the user's or guest's cart.

    The quantity parameter defines how many items of the selected beer should be
    added to the cart. If quantity is not provided, one item is added by default.

    Checks beer existence and available stock before creating or updating a cart item.
    """
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

    cart = await get_or_create_user_or_guest_cart(request=request, user=user, db=db, response=response)

    result = await db.execute(select(CartItem).where(CartItem.beer_id == beer_id, CartItem.cart_id == cart.id))
    cart_item = result.scalar_one_or_none()

    if cart_item is None:

        if beer.total_amount < quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"beer_id": "Not enough beer in stock."},
            )

        cart_item = CartItem(beer_id=beer_id, cart_id=cart.id, amount=quantity)
        db.add(cart_item)
        await db.flush()

    else:
        if cart_item.amount + quantity > beer.total_amount:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"beer_id": "Not enough beer in stock."},
            )

        cart_item.amount += quantity

    await db.commit()
    return await reload_and_format_cart(cart=cart, db=db)


@router.patch(
    "/{item_id}/",
    response_model=CartSchema,
    summary="Set cart item quantity",
    description="Set the exact quantity for a cart item. Deletes the cart item when its quantity reaches zero.",
    responses={
        404: {"description": "Cart or cart item not found."},
        409: {"description": "Beer is out of stock or requested amount exceeds stock."},
    },
)
async def set_cart_item_quantity(
    item_id: int,
    request: Request,
    quantity: int = Query(..., ge=0),
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Set the exact quantity for a cart item.

    The quantity parameter represents the final desired amount of this item in the cart,
    not the amount to add or remove.

    If quantity is zero, the cart item is removed.
    Checks that the requested quantity does not exceed available stock.
    """
    cart = await get_cart_or_404(request=request, user=user, db=db)

    result = await db.execute(
        select(CartItem)
        .where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id,
        )
        .options(selectinload(CartItem.beer))
    )
    cart_item = result.scalar_one_or_none()

    if cart_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"item_id": "Item not found."},
        )

    cart_item.amount = quantity

    if cart_item.amount <= 0:
        await db.delete(cart_item)

    if cart_item.amount > cart_item.beer.total_amount:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"beer_id": "Not enough beer in stock."},
        )

    await db.commit()
    return await reload_and_format_cart(cart=cart, db=db)


@router.delete(
    "/clear/",
    response_model=CartSchema,
    summary="Clear cart",
    description="Remove all items from the current authenticated or guest cart.",
    responses={
        404: {"description": "Cart not found."},
    },
)
async def clear_cart(
    request: Request,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_cart_or_404(request=request, user=user, db=db)

    for item in cart.cart_items:
        await db.delete(item)

    await db.commit()
    return await reload_and_format_cart(cart=cart, db=db)


@router.delete(
    "/{item_id}/",
    response_model=CartSchema,
    summary="Decrease cart item quantity",
    description="Decrease a cart item quantity by one. Deletes the cart item when its quantity reaches zero.",
    responses={
        404: {"description": "Cart or cart item not found."},
    },
)
async def remove_cart_item(
    item_id: int,
    request: Request,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Decrease a cart item quantity by one.

    If the cart item quantity reaches zero, the item is removed from the cart.
    """
    cart = await get_cart_or_404(request=request, user=user, db=db)

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
