"""Application configuration loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "no-reply@example.com")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

JWT_ACCESS_SECRET_KEY = os.environ["JWT_ACCESS_SECRET_KEY"]
JWT_REFRESH_SECRET_KEY = os.environ["JWT_REFRESH_SECRET_KEY"]
