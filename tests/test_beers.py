from decimal import Decimal

import pytest

from app.dependencies.enums import BeerTypeEnum
from app.models.beer import Beer


@pytest.fixture
def not_available_beer():
    return Beer(
        name="not_available_beer",
        description="test_beer_description",
        price=Decimal("10.20"),
        alcohol_percentage=Decimal("4.5"),
        is_filtered=True,
        beer_type=BeerTypeEnum.DARK,
        volume=330,
        total_amount=0,
    )


@pytest.fixture
def available_beer():
    return Beer(
        name="available_beer",
        description="test_beer_description",
        price=10.2,
        alcohol_percentage=4.5,
        is_filtered=True,
        beer_type=BeerTypeEnum.DARK,
        volume=330,
        total_amount=5,
    )


def test_beer_is_available_depends_on_total_amount_correctly(
    not_available_beer, available_beer
):
    assert not_available_beer.is_available is False
    assert available_beer.is_available is True
