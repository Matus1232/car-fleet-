# Car Fleet Manager

Webová aplikácia na správu vozového parku: autá, servisná história a dôležité termíny (STK, EK, poistenie, dialničná známka).

**Tech stack:** Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, React, Docker, GitHub Actions

## Spustenie

```bash
cp .env.example .env
docker compose up --build
```

Migrácie databázy (`alembic upgrade head`) sa spustia automaticky pri štarte API.
`docker-compose.override.yml` (live reload, `ENVIRONMENT=development`, teda zapnutý `/docs`) sa načíta sám;
produkčný beh: `docker compose -f docker-compose.yml up -d`.

- API: http://localhost:8000
- Swagger dokumentácia: http://localhost:8000/docs (len vo vývoji)
- Health check: http://localhost:8000/health

## Testy

Testy bežia nad **samostatnou** databázou (tabuľky sa pri nich mažú), preto vyžadujú `TEST_DATABASE_URL`:

```bash
docker compose exec db psql -U carfleet -d postgres -c "CREATE DATABASE carfleet_test"   # raz
cd backend
pip install -r requirements.txt -r requirements-dev.txt
TEST_DATABASE_URL=postgresql+psycopg://carfleet:change-me@localhost:5432/carfleet_test pytest
```

Vo Windows PowerShelli sa premenná nastavuje inak:

```powershell
$env:TEST_DATABASE_URL="postgresql+psycopg://carfleet:change-me@localhost:5432/carfleet_test"; pytest
```

CI (`.github/workflows/ci.yml`) na každý push a PR spúšťa lint (ruff), testy, kontrolu migrácií a build Docker image.

## Stav projektu

- [x] Štruktúra projektu, Docker Compose, PostgreSQL
- [x] Databázový model a migrácie
- [x] CRUD endpointy pre vozidlá
- [ ] Autentifikácia
- [x] Testy a CI
- [ ] Frontend
- [ ] Deployment
