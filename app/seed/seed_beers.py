"""Seed the local database with sample beer catalogue data."""

import asyncio
import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy import delete

from app.dependencies.enums import BeerTypeEnum, EventTypeEnum
from app.models.beer import Beer, BeerEventType
from db.engine import AsyncSessionLocal


async def seed_beers() -> None:
    """
    Replace existing beers with sample beer catalogue data.

    Loads beer data from beers_seed.json, deletes current beer records, and
    creates beers with their event type assignments.
    """
    seed_file_path = Path(__file__).parent / "beers_seed.json"

    with seed_file_path.open("r", encoding="utf-8") as file:
        beers_data = json.load(file)

    async with AsyncSessionLocal() as session:
        await session.execute(delete(Beer))

        for item in beers_data:
            beer = Beer(
                name=item["name"],
                description=item["description"],
                price=Decimal(str(item["price"])),
                image_url=item["image_url"],
                alcohol_percentage=Decimal(str(item["alcohol_percentage"])),
                is_filtered=item["is_filtered"],
                beer_type=BeerTypeEnum[item["beer_type"]],
                volume=item["volume"],
                total_amount=item["total_amount"],
            )
            beer.event_types = [
                BeerEventType(event_type=EventTypeEnum(event_type))
                for event_type in item.get("event_types", [])
            ]
            session.add(beer)

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_beers())
