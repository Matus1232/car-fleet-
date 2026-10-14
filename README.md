# Car Fleet Manager

Webová aplikácia na správu vozového parku. Aktuálna verzia (MVP) eviduje autá firmy
a má prihlásenie s rolami: admin autá spravuje, vodič ich vidí.

Plánované rozšírenia: servisná história a dôležité termíny (STK, EK, poistenie, diaľničná známka).

**Tech stack:** Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, React, TypeScript, Vite, Docker, GitHub Actions

## Štruktúra projektu

```
backend/    FastAPI aplikácia, databázové modely, migrácie (Alembic), testy
frontend/   React aplikácia (Vite + TypeScript)
docker-compose.yml           databáza + API
docker-compose.override.yml  vývojové nastavenie (načíta sa automaticky)
```

## Spustenie

Potrebuješ [Docker Desktop](https://www.docker.com/products/docker-desktop/) (backend a databáza)
a [Node.js](https://nodejs.org) vo verzii LTS (frontend).

### 1. Backend a databáza

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

### 2. Prvý admin

Verejná registrácia nie je. Prvého admina vytvoríš z terminálu (heslo sa vypýta):

```bash
docker compose exec api python -m app.cli create-admin --email admin@firma.sk
```

### 3. Frontend

V druhom termináli (backend musí bežať):

```bash
cd frontend
npm install        # len prvýkrát a po zmene package.json
npm run dev
```

Aplikácia beží na http://localhost:5173. Táto adresa musí byť v `CORS_ORIGINS` v `.env`,
inak prehliadač požiadavky na API zablokuje.

## Čo aplikácia vie

| | admin | vodič (`driver`) |
|---|---|---|
| Prihlásiť sa a odhlásiť | ✓ | ✓ |
| Zoznam áut so stránkovaním | ✓ | ✓ |
| Pridať, upraviť, zmazať auto | ✓ | – |
| Vytvárať používateľov | ✓ (zatiaľ len cez API) | – |

ŠPZ sa ukladá v jednotnom tvare: `ba 123-ab` sa uloží ako `BA123AB`, takže to isté auto
sa nedá zadať dvakrát.

## Prihlásenie a roly (API)

Všetky endpointy okrem `/health` vyžadujú prihlásenie (JWT token v hlavičke `Authorization: Bearer <token>`).

| Rola | Čo smie |
|---|---|
| `admin` | všetko: autá čítať, pridávať, upravovať, mazať; vytvárať používateľov (`POST /users`) |
| `driver` | autá len čítať |

Prihlásenie: `POST /auth/token` (formulár `username` = email, `password`) vráti `access_token`,
ktorý platí `ACCESS_TOKEN_EXPIRE_MINUTES` minút. `GET /auth/me` vráti prihláseného používateľa.
V `/docs` stačí kliknúť na **Authorize**.

Ochrana proti hádaniu hesiel: po 10 neúspešných pokusoch o prihlásenie z jednej IP adresy vracia
`/auth/token` chybu `429 Too Many Requests`, kým od najstaršieho z nich neuplynie 15 minút.

Nového používateľa vytvorí admin cez `POST /users`, napríklad vodiča:

```json
{ "email": "vodic@firma.sk", "password": "heslo1234", "role": "driver" }
```

## Frontend

Frontend je samostatná aplikácia, ktorá s backendom komunikuje cez `fetch`.
Prihlasovací token si ukladá v `localStorage`, takže obnovenie stránky nikoho neodhlási;
keď token vyprší, používateľa automaticky odhlási.

Adresa API je zatiaľ napevno v `frontend/src/api.ts` (`http://localhost:8000`).

Príkazy (v priečinku `frontend`):

| Príkaz | Čo robí |
|---|---|
| `npm run dev` | vývojový server s okamžitým obnovovaním pri zmene kódu |
| `npm run build` | kontrola typov (TypeScript) a produkčný build do `dist/` |
| `npm run lint` | kontrola kódu (oxlint) |

Popis súborov v `src/` je v [frontend/README.md](frontend/README.md).

## Testy

Backend testy bežia nad **samostatnou** databázou (tabuľky sa pri nich mažú), preto vyžadujú `TEST_DATABASE_URL`:

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

CI (`.github/workflows/ci.yml`) na každý push a PR spúšťa pre backend lint (ruff), testy, kontrolu migrácií
a build Docker image. Frontend zatiaľ v CI nie je.

## Stav projektu

- [x] Štruktúra projektu, Docker Compose, PostgreSQL
- [x] Databázový model a migrácie
- [x] CRUD endpointy pre vozidlá
- [x] Autentifikácia a roly (JWT), obmedzenie pokusov o prihlásenie
- [x] Testy a CI (backend)
- [x] Frontend (MVP): prihlásenie, zoznam áut, pridanie, úprava, mazanie
- [ ] Deployment
- [ ] Servisná história a termíny (STK, EK, poistenie, diaľničná známka)
