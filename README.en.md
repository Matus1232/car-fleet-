# Car Fleet Manager

[Slovenčina](README.md) | **English**

A web application for managing company cars and booking service appointments.

**Live:** https://fearless-rebirth-production-132141c8.up.railway.app

## Features

- **Sign-up and sign-in.** Anyone can create an account. An admin can only be created with a command on the server.
- **Service booking.** A monthly calendar; clicking a day shows hourly slots from 8:00 to 17:00.
  A slot can't be booked twice.
- **Bookings for the admin.** The admin sees who is coming and when, including the note, and can cancel bookings.
- **Fleet (admin only).** Cars with technical inspection (STK) validity, service history with costs, and an
  overview of cars whose inspection is expiring or overdue.
- **Price list** of services and an **e-shop** (coming soon).

## Architecture

```mermaid
flowchart LR
    U["Browser"] -- "HTTPS" --> R["Railway<br>(TLS, real client IP)"]
    R --> N["nginx<br>React app"]
    N -- "/api" --> A["FastAPI<br>backend"]
    A --> D[("PostgreSQL")]

    subgraph S["Railway private network"]
        A
        D
    end
```

Only the frontend is publicly reachable. nginx serves the React app to the browser and forwards
requests for `/api` to the backend. Neither the backend nor the database has a public address.

## Database

```mermaid
erDiagram
    users ||--o{ bookings : "books"
    vehicles ||--o{ service_records : "has"

    users {
        int id PK
        string email UK
        string hashed_password "Argon2 hash"
        string role "admin or driver"
        datetime created_at
    }
    bookings {
        int id PK
        int user_id FK
        date booking_date "unique together with hour"
        smallint hour "8 to 16"
        string note "optional"
        datetime created_at
    }
    vehicles {
        int id PK
        string brand
        string model
        string license_plate UK "normalized plate"
        date stk_valid_until "optional"
        datetime created_at
    }
    service_records {
        int id PK
        int vehicle_id FK
        string description
        numeric cost "not negative"
        date service_date
        datetime created_at
    }
    revoked_tokens {
        string jti PK "ID of a signed-out token"
        datetime expires_at
    }
    rate_limit_hits {
        int id PK
        string scope "login or register"
        string key "IP address"
        datetime created_at
    }
```

- A user can have many bookings, a car many service records. Deleting a user or a car also deletes
  their bookings or records (`ON DELETE CASCADE`).
- The day and hour pair is unique (`UNIQUE`). The database enforces it, so a slot can't be booked
  twice even when two people click at the same moment.
- `revoked_tokens` and `rate_limit_hits` aren't related to the other tables. They support signing out
  and limiting sign-in and sign-up attempts.

## Tech stack

| Part | What's used |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, Alembic (migrations), PostgreSQL |
| Frontend | React, TypeScript, Vite, React Router, plain CSS |
| Operations | Docker, nginx, Railway, GitHub Actions (tests and linting on every push) |

## Security

- Passwords are stored only as a hash (Argon2).
- The token (JWT) lives in an **httpOnly cookie** that JavaScript on the page can't read. The cookie is
  `Secure` and `SameSite=Strict`, and changes also require a CSRF header.
- **Signing out** revokes the token immediately, not only when it expires.
- Password guessing and mass sign-ups are **rate limited per IP address**. Attempts are stored in the
  database, so the limit survives restarts.
- Permissions are enforced by the backend (`401` when signed out, `403` when not allowed), not just by hidden buttons.
- nginx enforces HTTPS and sends security headers (HSTS, Content-Security-Policy).

## Structure

```
backend/    API: endpoints, database models, migrations, tests
frontend/   React app and nginx
```
