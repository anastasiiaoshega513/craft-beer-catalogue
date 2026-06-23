from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from db.engine import Base


class CartItem(Base):
    """
    Store one beer line in a cart.

    The same beer can appear only once per cart; the amount field stores its quantity.
    """

    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    beer_id = Column(Integer, ForeignKey("beers.id"), nullable=False)
    amount = Column(Integer, nullable=False, default=1)

    cart = relationship("Cart", back_populates="cart_items")
    beer = relationship("Beer")

    __table_args__ = (UniqueConstraint("cart_id", "beer_id", name="uq_cart_item_cart_id_beer_id"),)

    def __repr__(self) -> str:
        return f"<CartItem(id={self.id}, cart_id={self.cart_id}, beer_id={self.beer_id})>"


class Cart(Base):
    """Shopping cart owned either by an authenticated user or by a guest cookie."""

    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True)
    guest_id = Column(String(64), nullable=True, unique=True, index=True)

    user = relationship("User", back_populates="cart")

    cart_items = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        owner = f"user_id={self.user_id}" if self.user_id is not None else f"guest_id={self.guest_id}"
        return f"<Cart(id={self.id}, {owner})>"
