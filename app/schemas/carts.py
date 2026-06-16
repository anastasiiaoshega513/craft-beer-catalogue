from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CartItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    beer_id: int
    name: str
    quantity: int
    price: Decimal
    image_url: str | None = None


class CartSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    cart_items: list[CartItemSchema] = Field(default_factory=list)
    subtotal: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
