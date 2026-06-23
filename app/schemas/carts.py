from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CartItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    beer_id: int
    name: str
    quantity: int = Field(description="Quantity of this beer in the cart.")
    price: Decimal
    image_url: str | None = None


class CartSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = Field(
        default=None,
        description="Cart id is null when no cart exists yet.",
    )

    cart_items: list[CartItemSchema] = Field(
        default_factory=list,
        description="Items currently added to the cart.",
    )

    subtotal: Decimal = Field(
        default=Decimal("0"),
        description="Cart subtotal before delivery fee.",
    )

    total: Decimal = Field(
        default=Decimal("0"),
        description="Final cart total including delivery fee.",
    )
