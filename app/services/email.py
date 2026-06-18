"""Email sending helpers for account-related notifications."""

import smtplib
from email.message import EmailMessage

from app import config


def send_email(recipient: str, subject: str, body: str) -> None:
    """Send a plain text email using the configured SMTP server."""
    message = EmailMessage()

    message["From"] = config.SMTP_FROM_EMAIL
    message["To"] = recipient
    message["Subject"] = subject

    message.set_content(body)

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        if config.SMTP_USER and config.SMTP_PASSWORD:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)

        server.send_message(message)


def send_activation_email(recipient: str, activation_link: str) -> None:
    """Send an account activation email with the provided activation link."""
    subject = "Confirm your email"

    body = f"""
Hello!

Please confirm your email by clicking the link below:
{activation_link}
If you did not register, ignore this email.
"""

    send_email(
        recipient=recipient,
        subject=subject,
        body=body,
    )


def send_password_reset_email(recipient: str, reset_link: str) -> None:
    """Send a password reset email with the provided reset link."""
    subject = "Reset your password"

    body = f"""
Hello!

You requested a password reset for your account.
Please click the link below to create a new password:
{reset_link}
If you did not request a password reset, ignore this email.
    """

    send_email(
        recipient=recipient,
        subject=subject,
        body=body,
    )
