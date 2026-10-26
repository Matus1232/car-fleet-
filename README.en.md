# Car Fleet Manager

[Slovenčina](README.md) | **English**

A web application for managing company cars. A company can see which cars it has and add,
edit and delete them.

Users have two roles. An **admin** manages both cars and users. A **driver** can only view cars and
can't change anything. Sign-up isn't public: accounts are created by an admin, so nobody from outside
can get into the application.

This is the first version (MVP). Service history and deadline reminders, such as the technical
inspection (STK), emissions check, insurance and motorway vignette, will come later.

![List of cars in the application](docs/screenshots/vehicles-admin.png)

## Features

After signing in, the user sees a list of cars with the licence plate, make, model and date added,
10 cars per page. An admin has Edit and Delete buttons next to each car and an Add car button above the table.
A driver sees the same table without these buttons.

![Form for adding a car](docs/screenshots/vehicle-form.png)

A few things that aren't visible at first glance:

- **Licence plates are stored in one format.** `ba 123-ab`, `BA 123 AB` and `BA123AB` are the same
  car for the application, so it can't be entered twice.
- **Refreshing the page doesn't sign anyone out.** A session lasts 30 minutes (configurable in `.env`). When it expires,
  the application sends the user back to the sign-in page on their next action.
- **Passwords can't be guessed forever.** After 10 failed attempts from one IP address,
  signing in from it is blocked for 15 minutes.
- **Passwords aren't stored.** The database only keeps their hash (Argon2), from which the original
  password can't be recovered.

For now, an admin creates new users through the API; the application doesn't have a screen for it yet
(the steps are below in [Adding a driver](#adding-a-driver)).

## How it's built

The application has two separate parts that talk to each other over HTTP:

- **Backend (API)** in Python with the FastAPI framework. It stores data in PostgreSQL via SQLAlchemy
  and manages database changes with Alembic migrations.
- **Frontend** in React and TypeScript, built with Vite.

Everything runs in Docker: the database, the API and the web server with the frontend are three containers
started by a single command. Backend tests run in GitHub Actions after every push to `main` and on
every pull request.

```mermaid
flowchart LR
    W["Web server<br>port 5173"] -. "sends the app" .-> F["App<br>in the browser"]
    F -- "requests with a token" --> A["API<br>port 8000"]
    A -- "reads and writes" --> D[("Database")]
```

The web server sends the application to the browser only once, when the page is opened. After that,
the application talks only to the API: it asks for cars, sends changes and gets data back.

### Signing in

```mermaid
sequenceDiagram
    actor U as User
    participant F as App
    participant A as API
    participant D as Database

    U->>F: enters e-mail and password
    F->>A: sends credentials
    A->>D: looks up the user
    A->>A: verifies the password
    A-->>F: returns a token
    F->>F: stores the token
    F->>A: who am I?
    A-->>F: e-mail and role
    F->>A: give me the first 10 cars
    A-->>F: list of cars
```

The token is a signed "pass" that the application sends with every request from then on.
The API uses it to recognise who is asking, so it doesn't have to remember any sessions.

### Who can do what

```mermaid
flowchart TD
    R["Request for cars"] --> T{"Is the user<br>signed in?"}
    T -- no --> E1["Rejected<br>the app signs them out"]
    T -- yes --> W{"Do they want<br>to change something?"}
    W -- no --> OK["Gets the list of cars"]
    W -- yes --> AD{"Is it an admin?"}
    AD -- no --> E2["Rejected<br>not allowed"]
    AD -- yes --> OK2["Change is saved"]
```

Hiding buttons in the frontend is only a convenience for the driver. The real check happens in the backend,
so a driver can't delete a car even by sending a request straight to the API. In the code these are two functions
in [`backend/app/api/deps.py`](backend/app/api/deps.py): `get_current_user` finds out who is sending
the request (otherwise `401`), and `require_admin` checks that it's an admin (otherwise `403`).

### Database

| Table | Contents |
|---|---|
| `users` | e-mail (unique), password hash, role (`admin` or `driver`), creation date |
| `vehicles` | make, model, licence plate (unique), date added |

The tables aren't linked yet; cars aren't assigned to a specific driver.

## Getting started

You only need [Docker Desktop](https://www.docker.com/products/docker-desktop/) (it must be running)
and [Git](https://git-scm.com/). There's no need to install Python or Node.js; everything runs in containers.

### 1. Clone the project

```bash
git clone https://github.com/Matus1232/car-fleet-.git
```

Run the following commands in the project folder (`cd car-fleet-`).

### 2. Create a `.env` file

In the project folder, create a file named exactly `.env` (make sure Notepad doesn't turn it
into `.env.txt`) with this content:

```
POSTGRES_USER=carfleet
POSTGRES_PASSWORD=change-me
POSTGRES_DB=carfleet
CORS_ORIGINS=http://localhost:5173
SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

| Variable | Purpose |
|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | user, password and name of the database created on first start |
| `CORS_ORIGINS` | the address the browser is allowed to call the API from; without it the browser blocks requests |
| `SECRET_KEY` | secret key for signing tokens, at least 32 characters |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | how long a session lasts |

The file contains passwords, so it's in `.gitignore` and never gets into Git.

### 3. Generate a secret key

```bash
docker run --rm python:3.12-slim python -c "import secrets; print(secrets.token_hex(32))"
```

On the first run Docker downloads a Python image and then prints 64 random characters. Copy them into `.env` after `SECRET_KEY=`. Without the key the application
won't start; Docker prints the error `SECRET_KEY must be set in .env`.

### 4. Start the application

```bash
docker compose up --build
```

The first start takes a few minutes because Docker downloads and builds all the containers. The application is ready
when `Application startup complete` appears in the output. Database tables are created automatically.

| Address | What's there |
|---|---|
| http://localhost:5173 | the application |
| http://localhost:8000/docs | API documentation, where you can also try the API directly |
| http://localhost:8000/health | quick check that the API and database are running |

### 5. Create the first admin

The database starts empty and nobody can sign in, so you create the first admin from the terminal.
Open a second terminal (the first one keeps the application running) and run this in the project folder:

```bash
docker compose exec api python -m app.cli create-admin --email admin@company.com
```

The command asks for the password twice (at least 8 characters; you won't see it as you type). Then sign in
at http://localhost:5173.

### Adding a driver

1. Open http://localhost:8000/docs and click **Authorize** in the top right.
2. Enter the admin's e-mail as `username` and their password as `password`, then confirm.
3. Expand **POST /users**, click **Try it out**, paste the data and click **Execute**:

```json
{ "email": "driver@company.com", "password": "password1234", "role": "driver" }
```

If you write `admin` instead of `driver`, you create another admin.

### Stopping

Stop the application with `Ctrl+C` in the terminal where it's running, or with `docker compose down`.
Data in the database stays saved after stopping. To wipe it completely and start over,
use `docker compose down -v`.

### Development and production mode

`docker compose up` starts development mode. Docker automatically loads
`docker-compose.override.yml` with it. Code changes take effect right away: the frontend reloads in the browser
and the API restarts by itself.

`docker compose -f docker-compose.yml up -d` runs the application the way it would run on a server.
The frontend is built ahead of time into static files served by nginx, the API runs without automatic
restarts, and the documentation at `/docs` is turned off.

## Tests

The backend has tests in the `backend/tests` folder. They run outside Docker, so they need
[Python](https://www.python.org/downloads/) 3.12 or newer. The tests wipe tables on every run, so they
use their own database to avoid deleting the application's data.

Create the test database once, while the application is running:

```bash
docker compose exec db psql -U carfleet -d postgres -c "CREATE DATABASE carfleet_test"
```

Then install the libraries in the `backend` folder:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

Run the tests in PowerShell like this:

```powershell
$env:TEST_DATABASE_URL="postgresql+psycopg://carfleet:change-me@127.0.0.1:5432/carfleet_test"; pytest
```

In Git Bash, on Linux or on macOS like this:

```bash
TEST_DATABASE_URL=postgresql+psycopg://carfleet:change-me@127.0.0.1:5432/carfleet_test pytest
```

If your `.env` has a different database user or password, change them in these commands too. The address is
deliberately `127.0.0.1` and not `localhost`. On Windows, `localhost` is tried over IPv6 first, which
slows down every database connection so much that the tests take minutes instead of seconds.

GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs a code check (ruff), the tests
and a migration check, and builds the backend Docker image on every push to `main`
and on every pull request. The frontend isn't in CI yet.

## Frontend without Docker

When working on the frontend, you can also run it directly with [Node.js](https://nodejs.org) (LTS version).
The database and API keep running in Docker. First stop the frontend container, because it occupies
port 5173:

```bash
docker compose stop web
```

Then in the `frontend` folder:

| Command | What it does |
|---|---|
| `npm install` | installs libraries (the first time and after `package.json` changes) |
| `npm run dev` | starts the dev server; code changes show up in the browser right away |
| `npm run build` | checks types and builds the production version into `dist/` |
| `npm run lint` | checks the code (oxlint) |

The API address is hard-coded in [`frontend/src/api.ts`](frontend/src/api.ts) (`http://localhost:8000`).
A description of the individual frontend files is in [frontend/README.md](frontend/README.md) (in Slovak).

## Project structure

```
backend/                     API: endpoints, database models, migrations, tests
frontend/                    React application
docs/                        screenshots for the README
.github/                     CI and automatic dependency updates (Dependabot)
docker-compose.yml           database, API and frontend
docker-compose.override.yml  development settings, loaded by Docker automatically
```

## Project status

- [x] Docker Compose, PostgreSQL, database migrations
- [x] API for managing cars
- [x] Sign-in, roles and protection against password guessing
- [x] Backend tests and CI
- [x] Frontend: sign-in, car list, adding, editing, deleting
- [ ] Car service history
- [ ] Deadline reminders (technical inspection, emissions check, insurance, motorway vignette)
