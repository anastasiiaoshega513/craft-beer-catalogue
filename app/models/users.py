from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship, validates

from app.security.passwords import hash_password, verify_password
from app.validators import users as validators
from db.engine import Base


class User(Base):
    """User account model with write-only password handling and related auth records."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)

    email = Column(String, unique=True, nullable=False)
    _hashed_password = Column("hashed_password", String(255), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)

    activation_token = relationship(
        "ActivationToken",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )

    password_reset_token = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    cart = relationship(
        "Cart",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active})>"

    @classmethod
    def create(
        cls,
        email: str,
        raw_password: str,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> "User":
        """Create a user and hash the raw password through the password setter."""
        user = cls(email=email, first_name=first_name, last_name=last_name)
        user.password = raw_password
        return user

    @property
    def password(self) -> None:
        """Prevent reading password values from the user model."""
        raise AttributeError(
            "Password is write-only. Use the setter to set the password."
        )

    @password.setter
    def password(self, raw_password: str) -> None:
        validators.validate_password_strength(raw_password)
        self._hashed_password = hash_password(raw_password)

    def verify_password(self, raw_password: str) -> bool:
        """Check a raw password against the stored password hash."""
        return verify_password(raw_password, self._hashed_password)

    @validates("email")
    def validate_email(self, key: str, value: str) -> str:
        """Normalize and validate email addresses assigned to the model."""
        return validators.validate_email(value.lower())

    @validates("first_name", "last_name")
    def validate_name(self, key: str, value: str | None) -> str | None:
        """Normalize and validate first and last names assigned to the model."""
        if value is None:
            return value

        return validators.validate_name(value.lower(), key)
