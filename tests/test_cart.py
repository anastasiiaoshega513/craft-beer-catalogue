from decimal import Decimal

import pytest

from app.models.beer import Beer, BeerEventType
from app.models.carts import Cart, CartItem
from app.models.tokens import ActivationToken, PasswordResetToken, RefreshToken
from app.models.users import User
from services.carts import format_cart
from tests.test_beers import available_beer


@pytest.fixture
def cart():
    return Cart(
        id=1,
        user_id=1,
    )

@pytest.fixture
def cart_item_zero_amount():
    return CartItem(
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


# 2. Cart items formatting and totals
# format_cart() should include only valid cart items.
# Each item should contain id, beer_id, name, quantity, price, and image_url.
# subtotal should be calculated as price * quantity.
# total should include the delivery fee when the cart has at least one valid item.

# 3. Invalid cart item amounts
# format_cart() should ignore cart items with amount less than or equal to 0.
# If all cart items are ignored, subtotal and total should be 0.

# 4. Existing guest cookie
# get_or_create_guest_id() should return the existing guest_id from request cookies.
# It should not set a new cookie when guest_id already exists.

# 5. New guest cookie
# get_or_create_guest_id() should generate a new guest_id when the request has no guest_id cookie.
# It should set the guest_id cookie on the response with the expected cookie options.
# It should return the generated guest_id.
