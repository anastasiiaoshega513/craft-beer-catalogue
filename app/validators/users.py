import re

import email_validator


def validate_password_strength(password: str) -> str:
    errors = []

    if len(password) < 8:
        errors.append("- at least 8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("- at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("- at least one lower letter")
    if not re.search(r"\d", password):
        errors.append("- at least one digit")
    if not re.search(r"[@$!%*?&#]", password):
        errors.append("- at least one special character: @, $, !, %, *, ?, #, &")

    if errors:
        error_message = "Password must contain:\n" + "\n".join(errors)
        raise ValueError(error_message)

    return password


def validate_email(user_email: str) -> str:
    try:
        email_info = email_validator.validate_email(
            user_email, check_deliverability=False
        )
        email = email_info.normalized
    except email_validator.EmailNotValidError as error:
        raise ValueError(str(error))
    else:
        return email


def validate_name(name: str):
    if re.search(r"^[A-Za-z]*$", name) is None:
        raise ValueError(f"{name} contains non-english letters")
