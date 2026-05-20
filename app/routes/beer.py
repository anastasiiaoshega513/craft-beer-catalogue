from fastapi import APIRouter, Depends, HTTPException, status
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
async def get_beer_list(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Beer))
    beers = result.scalars().all()

    return {"beers": beers}

