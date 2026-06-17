# 1. User creation
# User.create() should create a User instance.
# The email should be normalized to lowercase.
# The raw password should not be stored in hashed_password.
# verify_password() should return True for the correct password.

# 2. Wrong password check
# verify_password() should return False for an incorrect password.

# 3. Write-only password field
# Reading user.password should raise AttributeError.

# 4. Weak password validation
# User.create() should raise ValueError when the password is too weak.

# 5. Token hashing
# hash_token() should return the same hash for the same token.
# hash_token() should return different hashes for different tokens.
