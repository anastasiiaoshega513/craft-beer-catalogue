from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CartItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    quantity: int
    price: Decimal
    image_url: str


class CartSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cart_items: list[CartItemSchema]
    subtotal: Decimal
    total: Decimal
