# auth-backend

FastAPI authentication service providing JWT-based login, registration, password reset, and token refresh.

---

## Overview

This service exposes a REST API under `/auth` and is designed to be run alongside a PostgreSQL database and the `auth-frontend` React application. It implements:

- Email/password registration and login
- Short-lived JWT access tokens with rotating refresh tokens
- Bcrypt password hashing
- SHA-256 hashed refresh and password-reset tokens (never stored in plaintext)
- Enumeration-resistant forgot-password flow
- Rate limiting on login and forgot-password endpoints
- SMTP-based password reset email delivery

---

## Project Structure

```
auth-backend/
├── app/
│   ├── main.py               # FastAPI application factory, CORS, router registration
│   ├── config.py             # Settings loaded from environment variables
│   ├── database.py           # SQLAlchemy engine and session factory
│   ├── dependencies.py       # Shared FastAPI dependencies (get_db, get_current_user)
│   ├── auth/
│   │   ├── router.py         # /auth/* route handlers
│   │   ├── service.py        # Business logic (login, register, refresh, reset, …)
│   │   └── schemas.py        # Pydantic request/response models
│   └── models/
│       ├── user.py           # User ORM model (users table)
│       ├── refresh_token.py  # RefreshToken ORM model (refresh_tokens table)
│       └── password_reset.py # PasswordReset ORM model (password_resets table)
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

---

## Endpoints

| Method | Path                    | Handler         | Description                              |
|--------|-------------------------|-----------------|------------------------------------------|
| POST   | `/auth/register`        | `register`      | Create a new user account                |
| POST   | `/auth/login`           | `login`         | Authenticate and receive tokens          |
| GET    | `/auth/me`              | `me`            | Return the authenticated user's profile  |
| POST   | `/auth/logout`          | `logout`        | Revoke the current refresh token         |
| POST   | `/auth/refresh`         | `refresh`       | Rotate refresh token, issue new access token |
| POST   | `/auth/forgot-password` | `forgotPassword` | Send a password reset email             |
| POST   | `/auth/reset-password`  | `resetPassword` | Consume reset token and set new password |

---

## Requirements

- Python 3.12+
- PostgreSQL 15+

Python dependencies are listed in `requirements.txt`:

```
fastapi
uvicorn[standard]
pydantic
sqlalchemy
psycopg[binary]
python-jose[cryptography]
passlib[bcrypt]
pytest
httpx
```

---

## Setup

### 1. Clone and enter the directory

```bash
git clone <repo-url>
cd auth-backend
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and fill in all values:

```bash
cp .env.example .env
```

See the [Environment Variables](#environment-variables) section below for details on each variable.

### 4. Apply the database schema

Run the SQL schema against your PostgreSQL instance:

```bash
psql "$DATABASE_URL" -f schema.sql
```

### 5. Start the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

---

## Docker

### Build the image

```bash
docker build -t auth-backend .
```

### Run the container

```bash
docker run --env-file .env -p 8000:8000 auth-backend
```

### Using Docker Compose (recommended)

From the repository root:

```bash
docker compose up --build
```

This starts both the PostgreSQL database and the auth-backend service together.

---

## Environment Variables

All variables must be set before starting the server. There are no built-in defaults for secrets.

### Database

| Variable       | Description                                      | Example                                              |
|----------------|--------------------------------------------------|------------------------------------------------------|
| `DATABASE_URL` | SQLAlchemy-compatible PostgreSQL connection URL  | `postgresql+psycopg://user:password@localhost:5432/auth_db` |

### JWT

| Variable                      | Description                                                  | Example          |
|-------------------------------|--------------------------------------------------------------|------------------|
| `JWT_SECRET_KEY`              | Secret used to sign access tokens. Use a long random string. | `change-me-to-a-long-random-secret` |
| `JWT_ALGORITHM`               | Signing algorithm for JWTs                                   | `HS256`          |
| `JWT_ACCESS_TOKEN_TTL_MINUTES`| Lifetime of access tokens in minutes                         | `15`             |

### Refresh Tokens

| Variable                              | Description                                                       | Example |
|---------------------------------------|-------------------------------------------------------------------|---------|
| `REFRESH_TOKEN_TTL_DAYS`              | Lifetime of refresh tokens when "remember me" is not selected     | `7`     |
| `REFRESH_TOKEN_TTL_REMEMBER_ME_DAYS`  | Lifetime of refresh tokens when "remember me" is selected         | `30`    |

### Password Hashing

| Variable        | Description                                         | Example |
|-----------------|-----------------------------------------------------|---------|
| `BCRYPT_ROUNDS` | Bcrypt cost factor (must be ≥ 12 per security policy) | `12`  |

### Password Reset

| Variable                    | Description                                    | Example |
|-----------------------------|------------------------------------------------|---------|
| `RESET_TOKEN_TTL_MINUTES`   | How long a password reset link remains valid   | `60`    |

### SMTP (Email)

| Variable         | Description                                      | Example                   |
|------------------|--------------------------------------------------|---------------------------|
| `SMTP_HOST`      | SMTP server hostname                             | `smtp.example.com`        |
| `SMTP_PORT`      | SMTP server port                                 | `587`                     |
| `SMTP_USERNAME`  | SMTP authentication username                     | `no-reply@example.com`    |
| `SMTP_PASSWORD`  | SMTP authentication password                     | `change-me`               |
| `SMTP_FROM`      | "From" address used in outgoing emails           | `no-reply@example.com`    |
| `SMTP_TLS`       | Enable STARTTLS (`true` or `false`)              | `true`                    |

### Rate Limiting

| Variable                                  | Description                                                       | Example |
|-------------------------------------------|-------------------------------------------------------------------|---------|
| `RATE_LIMIT_LOGIN_MAX`                    | Maximum login attempts allowed per window                         | `10`    |
| `RATE_LIMIT_LOGIN_WINDOW_SECONDS`         | Rolling window duration for login rate limiting (seconds)         | `60`    |
| `RATE_LIMIT_FORGOT_PASSWORD_MAX`          | Maximum forgot-password requests allowed per window               | `5`     |
| `RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS` | Rolling window duration for forgot-password rate limiting (seconds) | `60` |

### Application

| Variable      | Description                                                         | Example                    |
|---------------|---------------------------------------------------------------------|----------------------------|
| `APP_BASE_URL`| Base URL of the frontend application (used in reset email links)    | `http://localhost:3000`    |
| `CORS_ORIGIN` | Allowed CORS origin for the frontend                                | `http://localhost:3000`    |

---

## Running Tests

```bash
pytest
```

Tests cover the full auth flow: register → login → refresh → forgot-password → reset-password → logout, plus negative cases (duplicate email, weak password, password mismatch, expired token).

---

## Security Notes

- Passwords are hashed with bcrypt at the configured cost factor (minimum 12 rounds).
- Refresh tokens and password reset tokens are stored as SHA-256 hashes; plaintext tokens are never persisted or logged.
- Login and forgot-password endpoints are rate-limited per the configured environment variables.
- The forgot-password endpoint always returns the same response regardless of whether the email exists (enumeration resistance).
- Refresh tokens are rotated on every use and fully revoked on logout.
