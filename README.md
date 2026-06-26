# Craft Beer Catalogue API

Backend API for a craft beer shop built with FastAPI.

This repository contains the backend part of a team project. The project is currently in progress and is being developed by a team that includes a backend developer, frontend developer, project manager, data analyst, QA tester, and UI/UX designer.

The API covers user authentication, email account activation, password reset, JWT-based access and refresh tokens, beer catalogue features, and cart functionality for both guest and authenticated users.

## Status

In progress.

The `main` and `develop` branches are currently aligned, but deployment is currently connected to `develop` during active development.

Frontend integration and testing are still in progress, so the API structure and functionality may change.

## Deployment

The backend is deployed on Render.

API documentation is available here:

```text
https://craft-beer-catalogue-api.onrender.com/docs/
```

The project uses a PostgreSQL database hosted on Supabase.

Email sending is configured through Brevo SMTP.

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
* database cleanup script for old tokens and inactive users

## Tech stack

* Python
* FastAPI
* SQLAlchemy async
* Alembic
* Pydantic v2
* PostgreSQL
* Supabase
* JWT authentication
* Brevo SMTP
* Render
* GitHub Actions
* Pytest
* Black
* isort
* flake8

SQLite and Mailpit were used during earlier stages of development, but they are no longer part of the current runtime setup.

## Environment variables

A `.env.sample` file is provided in the repository with all required variables.

Create your own `.env` file in the project root based on this template and fill in the appropriate values for your environment.

```env
JWT_ACCESS_SECRET_KEY=
JWT_REFRESH_SECRET_KEY=

DATABASE_URL=

SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=

FRONTEND_URL=
```

## Running the project locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Apply database migrations:

```bash
alembic upgrade head
```

Run the FastAPI application:

```bash
uvicorn app.main:app --reload
```

The local API documentation will be available at:

```text
http://localhost:8000/docs
```

## Code quality and tests

The project uses GitHub Actions for continuous integration.

The CI workflow runs on pushes and pull requests for the main development branches and checks:

* import sorting with isort
* code formatting with Black
* linting with flake8
* tests with pytest

The same checks can be run locally:

```bash
isort --profile black --check-only .
black --check .
flake8 .
pytest
```

## Scheduled database cleanup

The project includes a scheduled GitHub Actions workflow for database cleanup.

The cleanup workflow runs once a week and executes the database cleanup script. It is used to remove old tokens and inactive users from the database.

The workflow can also be started manually from the GitHub Actions tab using `workflow_dispatch`.

## Project structure

```text
.
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI workflow for linting and tests
│       └── db_cleanup.yml      # scheduled database cleanup workflow
├── alembic/                    # database migrations
├── app/
│   ├── dependencies/           # FastAPI dependencies
│   ├── models/                 # SQLAlchemy models
│   ├── routes/                 # API routes
│   ├── schemas/                # Pydantic schemas
│   ├── scripts/                # maintenance scripts
│   │   └── cleanup_db.py       # database cleanup script
│   ├── security/               # authentication and security logic
│   ├── seed/                   # seed data
│   ├── services/               # business logic
│   ├── static/                 # static files
│   ├── validators/             # validation helpers
│   ├── __init__.py
│   ├── config.py               # environment-based configuration
│   └── main.py                 # FastAPI application entry point
├── db/
│   ├── __init__.py
│   ├── dependencies.py         # database session dependencies
│   └── engine.py               # database engine and session setup
├── tests/
│   ├── __init__.py
│   ├── test_beers.py
│   ├── test_cart.py
│   └── test_users.py
├── .env.sample                 # example environment variables
├── .flake8                     # flake8 configuration
├── .gitignore
├── alembic.ini                 # Alembic configuration
├── pyproject.toml              # project/tooling configuration
├── requirements.txt            # project dependencies
└── README.md
```

