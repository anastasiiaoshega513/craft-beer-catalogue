# Craft Beer Shop API

Backend API for a craft beer shop built with FastAPI.

This repository contains the backend part of a team project. The project is currently in progress and is being developed by a team that includes a backend developer, frontend developer, project manager, data analyst, QA tester, and designer.

The API covers user authentication, email account activation, password reset, JWT-based access and refresh tokens, beer catalogue features, and cart functionality for both guest and authenticated users.

## Status

In progress.

The active development branch is `develop`. The `main` branch is kept stable and may not include the latest work yet.

## Implemented features

* user registration
* email account activation
* login and logout
* JWT access and refresh tokens
* refresh token storage in the database
* password reset flow
* beer catalogue
* product details
* filtering, sorting, search, and pagination for beer listings
* guest cart using cookies
* cart for authenticated users
* adding, removing, and clearing cart items
* stock checks for cart operations
* local email testing with Mailpit

## Tech stack

* Python
* FastAPI
* SQLAlchemy async
* Alembic
* Pydantic v2
* SQLite for local development
* PostgreSQL planned for deployment
* JWT authentication
* Mailpit for local email testing

## API documentation

FastAPI provides interactive API documentation through Swagger UI.

When the backend is running locally, the API documentation is available at:

```text
http://localhost:8000/docs
```

## Notes

This project is still under development, so the API structure and functionality may change.
