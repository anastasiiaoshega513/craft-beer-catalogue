import smtplib
from email.message import EmailMessage

from app import config


def send_email(to_whom: str, subject: str, body: str) -> None:
    message = EmailMessage()

    message["From"] = config.SMTP_FROM_EMAIL
    message["To"] = to_whom
    message["Subject"] = subject

    message.set_content(body)

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        if config.SMTP_USER and config.SMTP_PASSWORD:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)

        server.send_message(message)
