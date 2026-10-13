# Car Fleet Manager

Webová aplikácia na správu vozového parku: autá, servisná história a dôležité termíny (STK, EK, poistenie, dialničná známka).

**Tech stack:** Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, React, Docker, GitHub Actions

## Spustenie

V koreni projektu vytvor súbor `.env` (do Gitu sa nedáva):

```
POSTGRES_USER=carfleet
POSTGRES_PASSWORD=change-me
POSTGRES_DB=carfleet
DATABASE_URL=postgresql+psycopg://carfleet:change-me@localhost:5432/carfleet
APP_NAME=Car Fleet Manager
CORS_ORIGINS=http://localhost:5173
SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

```bash
python -c "import secrets; print(secrets.token_hex(32))"   # výsledok vlož do .env ako SECRET_KEY
docker compose up --build
```

Migrácie databázy (`alembic upgrade head`) sa spustia automaticky pri štarte API.
`docker-compose.override.yml` (live reload, `ENVIRONMENT=development`, teda zapnutý `/docs`) sa načíta sám;
produkčný beh: `docker compose -f docker-compose.yml up -d`.

- API: http://localhost:8000
- Swagger dokumentácia: http://localhost:8000/docs (len vo vývoji)
- Health check: http://localhost:8000/health

## Prihlásenie a roly

Všetky endpointy okrem `/health` vyžadujú prihlásenie (JWT token v hlavičke `Authorization: Bearer <token>`).

| Rola | Čo smie |
|---|---|
| `admin` | všetko: autá čítať, pridávať, upravovať, mazať; vytvárať používateľov (`POST /users`) |
| `driver` | autá len čítať |

Verejná registrácia nie je, používateľov vytvára admin. Prvého admina vytvoríš z terminálu (heslo sa vypýta):

```bash
docker compose exec api python -m app.cli create-admin --email admin@firma.sk
```

Prihlásenie: `POST /auth/token` (formulár `username` = email, `password`) vráti `access_token`.
`GET /auth/me` vráti prihláseného používateľa. V `/docs` stačí kliknúť na **Authorize**.

## Testy

Testy bežia nad **samostatnou** databázou (tabuľky sa pri nich mažú), preto vyžadujú `TEST_DATABASE_URL`:

```bash
docker compose exec db psql -U carfleet -d postgres -c "CREATE DATABASE carfleet_test"   # raz
cd backend
pip install -r requirements.txt -r requirements-dev.txt
TEST_DATABASE_URL=postgresql+psycopg://carfleet:change-me@127.0.0.1:5432/carfleet_test pytest
```

Vo Windows PowerShelli sa premenná nastavuje inak:

```powershell
$env:TEST_DATABASE_URL="postgresql+psycopg://carfleet:change-me@127.0.0.1:5432/carfleet_test"; pytest
```

Používaj `127.0.0.1`, nie `localhost`: na Windows sa `localhost` najprv skúša cez IPv6 a každé pripojenie
k databáze sa spomalí (testy potom bežia minúty namiesto sekúnd).

CI (`.github/workflows/ci.yml`) na každý push a PR spúšťa lint (ruff), testy, kontrolu migrácií a build Docker image.

## Stav projektu

- [x] Štruktúra projektu, Docker Compose, PostgreSQL
- [x] Databázový model a migrácie
- [x] CRUD endpointy pre vozidlá
- [x] Autentifikácia a roly (JWT)
- [x] Testy a CI
- [ ] Frontend
- [ ] Deployment
