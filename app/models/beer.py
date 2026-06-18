from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.dependencies.enums import BeerTypeEnum, EventTypeEnum
from db.engine import Base


class BeerEventType(Base):
    """Store one event type assigned to a beer."""

    __tablename__ = "beer_event_types"

    beer_id = Column(
        Integer, ForeignKey("beers.id", ondelete="CASCADE"), primary_key=True
    )
    event_type = Column(Enum(EventTypeEnum), primary_key=True, nullable=False)

    beer = relationship("Beer", back_populates="event_types")

    def __repr__(self) -> str:
        return f"<BeerEventType={self.event_type}, beer_id={self.beer_id}>"


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

    event_types = relationship(
        "BeerEventType",
        back_populates="beer",
        cascade="all, delete-orphan",
    )

    @property
    def event_type(self) -> list[EventTypeEnum]:
        """Return event type enum values instead of BeerEventType relationship objects."""
        return [event.event_type for event in self.event_types]

    @property
    def is_available(self) -> bool:
        """Return whether the beer has stock available for cart operations."""
        return self.total_amount > 0

    def __repr__(self) -> str:
        return f"<Beer={self.name}>"
