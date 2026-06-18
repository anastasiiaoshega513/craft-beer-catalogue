import pytest

from app.models.beer import Beer, BeerEventType
from app.models.carts import Cart, CartItem
from app.models.tokens import ActivationToken, PasswordResetToken, RefreshToken
from app.models.users import User
from app.security.secure_token import hash_token


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


def test_token_is_hashed_correctly():
    token = "test-token"
    same_token = "test-token"
    another_token = "another-token"

    token_hash = hash_token(token)
    same_token_hash = hash_token(same_token)
    another_token_hash = hash_token(another_token)

    assert token_hash == same_token_hash
    assert token_hash != another_token_hash
    assert token_hash != token
