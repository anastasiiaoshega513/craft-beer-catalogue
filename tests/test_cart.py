from decimal import Decimal

import pytest
from fastapi import Request, Response

from app.models.beer import Beer, BeerEventType
from app.models.carts import Cart, CartItem
from app.models.tokens import ActivationToken, PasswordResetToken, RefreshToken
from app.models.users import User
from app.security.guest_user import get_or_create_guest_id
from app.services.carts import format_cart


@pytest.fixture
def cart():
    return Cart(
        id=1,
        user_id=1,
    )


@pytest.fixture
def cart_item_zero_amount():
    return CartItem(
        id=1,
        cart_id=1,
        beer_id=1,
        amount=0,
    )


@pytest.fixture
def cart_item_positive_amount():
    beer = Beer(
        id=2,
        name="Test Beer",
        price=Decimal("10.00"),
        image_url="/test.jpg",
    )

    return CartItem(
        id=2,
        cart_id=1,
        beer_id=2,
        amount=3,
        beer=beer,
    )


@pytest.mark.asyncio
async def test_format_non_existing_cart_should_return_empty_cart():
    result = await format_cart(None)

    assert result == {
        "id": None,
        "cart_items": [],
        "subtotal": 0,
        "total": 0,
    }


@pytest.mark.asyncio
async def test_cart_items_and_totals_are_formatted_correctly(cart, cart_item_positive_amount, cart_item_zero_amount):
    cart.cart_items = [
        cart_item_positive_amount,
        cart_item_zero_amount,
    ]
    result = await format_cart(cart)

    expected_subtotal = cart_item_positive_amount.beer.price * cart_item_positive_amount.amount

    returned_item_ids = [item["id"] for item in result["cart_items"]]

    assert cart_item_positive_amount.id in returned_item_ids
    assert cart_item_zero_amount.id not in returned_item_ids
    assert result["id"] == cart.id
    assert result["total"] == expected_subtotal + 5


@pytest.mark.asyncio
async def test_invalid_cart_item_amounts_are_ignored(cart, cart_item_zero_amount):
    cart.cart_items = [cart_item_zero_amount]

    result = await format_cart(cart)

    assert result["cart_items"] == []
    assert result["subtotal"] == 0
    assert result["total"] == 0


def test_existing_guest_cookie_should_be_returned_without_setting_new_cookie():
    existing_guest_id = "existing-guest-id"

    request = Request(
        {
            "type": "http",
            "headers": [
                (b"cookie", f"guest_id={existing_guest_id}".encode()),
            ],
        }
    )
    response = Response()

    result = get_or_create_guest_id(request, response)

    assert result == existing_guest_id
    assert "set-cookie" not in response.headers


def test_new_guest_cookie_should_be_set_and_returned():
    request = Request(
        {
            "type": "http",
            "headers": [],
        }
    )
    response = Response()

    result = get_or_create_guest_id(request, response)

    assert result
    assert "set-cookie" in response.headers
    assert f"guest_id={result}" in response.headers["set-cookie"]
