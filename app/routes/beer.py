from typing import Literal

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession

from db.dependencies import get_db
from app.models.beer import Beer
from app.schemas.beer import BeerListSchema
from app.dependencies.enums import BeerTypeEnum, AlcoholRangeEnum
from app.schemas.beer import BeerDetailSchema

router = APIRouter(
    prefix="/beers",
    tags=["Beers"],
)


@router.get("/", response_model=BeerListSchema)
async def get_beer_list(
        offset: int = Query(0, ge=0),
        search: str | None = Query(None, alias="search"),
        beer_type: BeerTypeEnum | None = Query(None, alias="type"),
        alcohol_range: AlcoholRangeEnum | None = Query(None, alias="alcohol"),
        filtered: bool = Query(None, alias="filtered"),
        sort_by: Literal["id", "price"] = "id",
        sort_order: Literal["asc", "desc"] = "asc",
        db: AsyncSession = Depends(get_db)
):
    if sort_order == "asc":
        order_by = asc(sort_by)
    else:
        order_by = desc(sort_by)

    filters = []

    if beer_type is not None:
        filters.append(Beer.beer_type == beer_type.value)

    if alcohol_range == AlcoholRangeEnum.FOUR_SIX:
        filters.append(Beer.alcohol_percentage >= 4)
        filters.append(Beer.alcohol_percentage < 6)
    elif alcohol_range == AlcoholRangeEnum.SIX_EIGHT:
        filters.append(Beer.alcohol_percentage >= 6)
        filters.append(Beer.alcohol_percentage < 8)
    elif alcohol_range == AlcoholRangeEnum.EIGHT_PLUS:
        filters.append(Beer.alcohol_percentage >= 8)

    if filtered is not None:
        filters.append(Beer.is_filtered.is_(filtered))

    if search:
        search_pattern = f"%{search.strip()}%"
        filters.append(Beer.name.ilike(search_pattern))

    limit = 6

    result = await db.execute(
        select(Beer)
        .order_by(order_by)
        .where(*filters)
        .offset(offset)
        .limit(limit + 1)
    )

    beers = result.scalars().all()

    if len(beers) > limit:
        beers = beers[:limit]
        next_offset = offset + limit
    else:
        next_offset = None

    return {
        "beers": beers,
        "next_offset": next_offset,
    }


@router.get("/{beer_id}/", response_model=BeerDetailSchema)
async def get_beer_detail(beer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Beer).where(Beer.id == beer_id))
    beer = result.scalar_one_or_none()

    if beer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beer not found")

    return beer
