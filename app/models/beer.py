from enum import StrEnum, auto

from sqlalchemy import Column, Integer, String, Text, Numeric, Enum, Boolean

from db.engine import Base


class BeerTypeEnum(StrEnum):
    DARK = auto()
    LIGHT = auto()


class Beer(Base):
    __tablename__ = "beers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    image_url = Column(String, nullable=True)

    alcohol_percentage = Column(Numeric(4, 2), nullable=False)
    is_filtered = Column(Boolean, nullable=False)
    beer_type = Column(Enum(BeerTypeEnum), nullable=False)
    volume = Column(Integer, nullable=False)
    total_amount = Column(Integer, nullable=False, default=0)


    def __repr__(self):
        return f"<Beer={self.name}>"
