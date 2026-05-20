from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.dependencies.enums import BeerTypeEnum


class BeerBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    price: Decimal
    image_url: str | None = None
    alcohol_percentage: Decimal
    is_filtered: bool
    beer_type: BeerTypeEnum
    volume: int
    is_available: bool


class BeerListItemSchema(BeerBaseSchema):
    id: int


class BeerListSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    beers: list[BeerListItemSchema]


class BeerDetailSchema(BeerBaseSchema):

    id: int
    description: str
