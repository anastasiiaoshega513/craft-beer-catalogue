from enum import StrEnum, auto


class BeerTypeEnum(StrEnum):
    DARK = auto()
    LIGHT = auto()


class AlcoholRangeEnum(StrEnum):
    FOUR_SIX = "4-6"
    SIX_EIGHT = "6-8"
    EIGHT_PLUS = "8-plus"
