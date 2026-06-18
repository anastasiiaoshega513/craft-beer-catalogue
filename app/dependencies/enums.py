"""Enums used for beer catalogue data and filters."""

from enum import StrEnum, auto


class BeerTypeEnum(StrEnum):
    DARK = auto()
    LIGHT = auto()


class AlcoholRangeEnum(StrEnum):
    FOUR_SIX = "4-6"
    SIX_EIGHT = "6-8"
    EIGHT_PLUS = "8-plus"


class EventTypeEnum(StrEnum):
    AFTER_WORK = "after-work"
    WEEKEND_ESCAPE = "weekend-escape"
    FRIENDS_OVER = "friends-over"
    AFTER_MIDNIGHT = "after-midnight"
    DINNER_AND_DRINKS = "dinner-and-drinks"
