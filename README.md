# Old Barrel Backend API

Backend API for **Old Barrel**, a craft beer catalogue and online shop application built with **FastAPI**.

This repository contains the backend part of a team project. The backend provides the main data layer and business logic for the application, including user authentication, email verification, beer catalogue functionality, product details, and cart operations.

The project was developed as a cross-functional team project with the following roles: Project Manager, UI/UX Designer, Data Analyst, Frontend Developer, Backend Developer, and QA Engineer.

## Live API

The backend is deployed on **Render**.

API documentation is available through Swagger:

```text
https://craft-beer-catalogue-api.onrender.com/docs/
```

The project uses a PostgreSQL database hosted on **Supabase**.

Email sending is configured through **Brevo SMTP**.

## Backend functionality

The backend API supports the main application flows:

* user registration
* email account activation
* login and logout
* password reset flow
* JWT-based access and refresh token authentication
* refresh token storage in the database
* beer catalogue data
* product detail pages
* search, filtering, sorting, and pagination
* stock validation for cart updates
* scheduled database cleanup for old tokens and inactive users
* guest cart using cookies
* cart for authenticated users
* adding, removing, and clearing cart items 
* stock checks for cart operations

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

A `.env.sample` file is provided in the repository with the required environment variables.

Create a local `.env` file in the project root based on this template and fill in the values for your environment.

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

Local API documentation will be available at:

```text
http://localhost:8000/docs
```

## Tests and code quality

The project uses GitHub Actions for continuous integration.

The CI workflow runs on pushes and pull requests for the main development branches and checks:

* import sorting with isort
* code formatting with Black
* linting with flake8
* tests with Pytest

The same checks can be run locally:

```bash
isort --profile black --check-only .
black --check .
flake8 .
pytest
```

## Scheduled database cleanup

The project includes a scheduled GitHub Actions workflow for database cleanup.

The cleanup workflow runs once a week and executes the database cleanup script. It removes old tokens and inactive users from the database to reduce unnecessary stored data.

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
