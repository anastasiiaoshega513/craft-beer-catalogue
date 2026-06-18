import pytest

from app.models.users import User
from app.models.carts import Cart, CartItem
from app.models.beer import Beer, BeerEventType
from app.models.tokens import RefreshToken, PasswordResetToken, ActivationToken


@pytest.fixture
def user():
    return User.create(
        email="TEST@EMAIL.COM",
        raw_password="StrongPass123!",
        first_name="Test",
        last_name="User",
    )


def test_user_create_with_email_lower_and_correct_hashed_password(user):
    assert isinstance(user, User)
    assert user.email == "test@email.com"
    assert user._hashed_password != "StrongPass123!"
    assert user.verify_password("StrongPass123!") is True


def test_verify_incorrect_password_returns_false(user):
    assert user.verify_password("WrongPass123!") is False


def test_password_read_raises_attribute_error(user):
    with pytest.raises(AttributeError):
        user.password


def test_user_creation_with_weak_password_raises_value_error(user):
    with pytest.raises(ValueError):
        User.create(
            email="test@email.com",
            raw_password="weak",
        )

# 5. Token hashing
# hash_token() should return the same hash for the same token.
# hash_token() should return different hashes for different tokens.
