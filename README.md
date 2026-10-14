# Car Fleet Manager

Webová aplikácia na správu vozového parku. Aktuálna verzia (MVP) eviduje autá firmy
a má prihlásenie s rolami: admin autá spravuje, vodič ich vidí.

Plánované rozšírenia: servisná história a dôležité termíny (STK, EK, poistenie, diaľničná známka).

**Tech stack:** Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, React, TypeScript, Vite, Docker, GitHub Actions

## Ukážka

Zoznam áut (prihlásený admin):

![Zoznam áut](docs/screenshots/vehicles-admin.png)

Pridanie auta:

![Formulár na pridanie auta](docs/screenshots/vehicle-form.png)

## Štruktúra projektu

```
backend/    FastAPI aplikácia, databázové modely, migrácie (Alembic), testy
frontend/   React aplikácia (Vite + TypeScript)
docs/       screenshoty
docker-compose.yml           databáza + API + frontend
docker-compose.override.yml  vývojové nastavenie (načíta sa automaticky)
```

## Architektúra

```mermaid
flowchart LR
    subgraph browser["Prehliadač"]
        F["React aplikácia"]
    end
    F -- "fetch + JWT token<br>JSON" --> A
    subgraph docker["Docker Compose"]
        W["web: Vite / nginx<br>:5173"]
        A["api: FastAPI<br>:8000"] -- "SQLAlchemy" --> D[("db: PostgreSQL<br>:5432")]
    end
    W -. "HTML, JS, CSS" .-> F
```

Frontend a backend sú dva samostatné programy. Kontajner `web` pošle prehliadaču súbory aplikácie,
tá potom komunikuje už len s API: posiela požiadavky s tokenom a dostáva späť JSON.

### Prihlásenie

```mermaid
sequenceDiagram
    actor U as Používateľ
    participant F as Frontend
    participant A as API
    participant D as Databáza

    U->>F: e-mail a heslo
    F->>A: POST /auth/token
    A->>D: nájdi používateľa podľa e-mailu
    A->>A: over heslo voči Argon2 hashu
    A-->>F: access_token (JWT)
    F->>F: ulož token do localStorage
    F->>A: GET /auth/me (Authorization: Bearer token)
    A-->>F: e-mail a rola
    F->>A: GET /vehicles?skip=0&limit=10
    A-->>F: autá a celkový počet
```

### Overenie každej požiadavky

```mermaid
flowchart TD
    R["Požiadavka na /vehicles"] --> T{"Platný token?<br>(get_current_user)"}
    T -- nie --> E401["401 Unauthorized<br>frontend odhlási používateľa"]
    T -- áno --> W{"Zápis?<br>POST, PATCH, DELETE"}
    W -- nie --> OK["200 OK"]
    W -- áno --> AD{"Rola admin?<br>(require_admin)"}
    AD -- nie --> E403["403 Forbidden"]
    AD -- áno --> OK2["Zmena sa vykoná"]
```

**Autentifikácia** (kto si) robí `get_current_user`, **autorizáciu** (čo smieš) `require_admin`
v `backend/app/api/deps.py`.

### Databáza

```mermaid
erDiagram
    users {
        int id PK
        string email UK
        string hashed_password
        string role "admin alebo driver"
        datetime created_at
    }
    vehicles {
        int id PK
        string brand
        string model
        string license_plate UK "napr. BA123AB"
        datetime created_at
    }
```

Tabuľky zatiaľ nie sú prepojené: autá nepatria konkrétnemu vodičovi.

## Spustenie

Stačí [Docker Desktop](https://www.docker.com/products/docker-desktop/). Databáza, API aj frontend
sa spustia jedným príkazom.

### 1. Nastavenie a spustenie

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

| Režim | Príkaz | Frontend | API |
|---|---|---|---|
| vývoj | `docker compose up` | Vite dev server, zmena v kóde sa hneď prejaví v prehliadači | live reload, zapnutý `/docs` |
| produkcia | `docker compose -f docker-compose.yml up -d` | hotový build, posiela ho nginx | bez reloadu, `/docs` vypnuté |

Vo vývoji sa `docker-compose.override.yml` načíta automaticky.

- Aplikácia: http://localhost:5173
- API: http://localhost:8000
- Swagger dokumentácia: http://localhost:8000/docs (len vo vývoji)
- Health check: http://localhost:8000/health

### 2. Prvý admin

Verejná registrácia nie je. Prvého admina vytvoríš z terminálu (heslo sa vypýta):

```bash
docker compose exec api python -m app.cli create-admin --email admin@firma.sk
```

Potom sa prihlás na http://localhost:5173. Táto adresa musí byť v `CORS_ORIGINS` v `.env`,
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

Adresa API je napevno v `frontend/src/api.ts` (`http://localhost:8000`). Prehliadač volá API priamo,
aj keď frontend beží v Dockeri.

Frontend sa dá spustiť aj bez Dockeru, potrebuješ na to [Node.js](https://nodejs.org) vo verzii LTS.
Najprv zastav kontajner (`docker compose stop web`), lebo obsadzuje port 5173. Príkazy v priečinku `frontend`:

| Príkaz | Čo robí |
|---|---|
| `npm install` | nainštaluje knižnice (prvýkrát a po zmene `package.json`) |
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
