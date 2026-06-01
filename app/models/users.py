from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.orm import validates

from app.validators import users as validators
from db.engine import Base
from app.security.passwords import verify_password, hash_password


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)

    email = Column(String, unique=True, nullable=False)
    _hashed_password = Column("hashed_password", String(255), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active})>"

    @classmethod
    def create(cls, email: str, raw_password: str) -> "User":
        user = cls(email=email)
        user.password = raw_password
        return user

    @property
    def password(self) -> None:
        raise AttributeError("Password is write-only. Use the setter to set the password.")

    @password.setter
    def password(self, raw_password: str) -> None:
        validators.validate_password_strength(raw_password)
        self._hashed_password = hash_password(raw_password)

    def verify_password(self, raw_password: str) -> bool:
        return verify_password(raw_password, self._hashed_password)

    @validates("email")
    def validate_email(self, key, value):
        return validators.validate_email(value.lower())

    @validates("first_name", "last_name")
    def validate_name(self, _key, value):
        if value is None:
            return value

        validators.validate_name(value)
        return value
