from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.dependencies.enums import BeerTypeEnum, EventTypeEnum


class BeerBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal
    image_url: str | None = None
    alcohol_percentage: Decimal
    is_filtered: bool
    beer_type: BeerTypeEnum
    volume: int
    is_available: bool
    event_type: list[EventTypeEnum] = Field(
        default_factory=list,
        description="Event categories assigned to the beer.",
    )


class BeerListItemSchema(BeerBaseSchema):
    pass


class BeerListSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    beers: list[BeerListItemSchema]
    next_offset: int | None = Field(
        default=None,
        description="Offset for the next page. Null when there are no more beers.",
    )


class BeerDetailSchema(BeerBaseSchema):
    description: str
