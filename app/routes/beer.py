from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.dependencies import get_db
from app.models.beer import Beer
from app.schemas.beer import BeerListSchema

router = APIRouter(
    prefix="/beers",
    tags=["Beers"],
)


@router.get("/", response_model=BeerListSchema)
async def get_beer_list(
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db)
):
    limit = 6

    result = await db.execute(
        select(Beer)
        .order_by(Beer.id)
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
