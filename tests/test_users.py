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


# 2. Wrong password check
# verify_password() should return False for an incorrect password.

# 3. Write-only password field
# Reading user.password should raise AttributeError.

# 4. Weak password validation
# User.create() should raise ValueError when the password is too weak.

# 5. Token hashing
# hash_token() should return the same hash for the same token.
# hash_token() should return different hashes for different tokens.
