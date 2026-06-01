from sqlalchemy import Column, Integer, String, Text, Numeric, Enum, Boolean, CheckConstraint

from db.engine import Base
from app.dependencies.enums import BeerTypeEnum


class Beer(Base):
    __tablename__ = "beers"

    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="check_total_amount_non_negative"),
    )

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

    @property
    def is_available(self) -> bool:
        return self.total_amount > 0

    def __repr__(self):
        return f"<Beer={self.name}>"
