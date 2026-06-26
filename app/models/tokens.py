from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.security.secure_token import generate_secure_token
from db.engine import Base


class BaseToken(Base):
    """
    Base model for raw user tokens that expire by default after one day.

    Used by activation and password reset tokens, where each user can have
    only one active token of that type.
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, nullable=False, default=generate_secure_token)
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=1),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)


class ActivationToken(BaseToken):
    """Token used to activate a newly registered user account."""

    __tablename__ = "activation_tokens"

    user = relationship("User", back_populates="activation_token")

    def __repr__(self) -> str:
        return f"<ActivationTokenModel(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


class PasswordResetToken(BaseToken):
    """Token used to authorize a password reset request."""

    __tablename__ = "password_reset_tokens"

    user = relationship("User", back_populates="password_reset_token")

    def __repr__(self) -> str:
        return f"<PasswordResetTokenModel(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


class RefreshToken(Base):
    """Hashed refresh token record used to issue new access tokens."""

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)

    token_hash = Column(String(64), unique=True, nullable=False, index=True)

    expires_at = Column(DateTime(timezone=True), nullable=False)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
