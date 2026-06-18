"""Validation rules for user passwords, email addresses, and names."""

import re

import email_validator


def validate_password_strength(password: str) -> str:
    """
    Validate password complexity and return the password if it passes.

    Raises ValueError with all missing password requirements.
    """
    errors = []

    if len(password) < 8:
        errors.append("at least 8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("at least one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("at least one digit")
    if not re.search(r"[@$!%*?&#]", password):
        errors.append("at least one special character: @, $, !, %, *, ?, #, &")

    if errors:
        raise ValueError({"password": errors})

    return password


def validate_email(user_email: str) -> str:
    """Normalize and validate an email address."""
    try:
        email_info = email_validator.validate_email(
            user_email, check_deliverability=False
        )
        email = email_info.normalized
    except email_validator.EmailNotValidError:
        raise ValueError({"email": "Invalid email address."})
    else:
        return email


def validate_name(name: str, field_name: str) -> str:
    """Validate that a name contains only English letters."""
    if re.search(r"^[A-Za-z]+$", name) is None:
        raise ValueError({field_name: "Only English letters are allowed."})
    return name
