# Car Fleet Manager

**Slovenčina** | [English](README.en.md)

Webová aplikácia na správu firemných áut. Firma v nej vidí, aké autá má, a môže ich pridávať,
upravovať a mazať.

Používatelia majú dve roly. **Admin** spravuje autá aj používateľov. **Vodič** autá len vidí a nič
nezmení. Registrácia nie je verejná: účty zakladá admin, takže sa do aplikácie nedostane nikto zvonka.

Toto je prvá verzia (MVP). Neskôr pribudne servisná história áut a pripomienky termínov, ako STK,
emisná kontrola, poistenie a diaľničná známka.

![Zoznam áut v aplikácii](docs/screenshots/vehicles-admin.png)

## Čo aplikácia vie

Po prihlásení sa zobrazí zoznam áut s ŠPZ, značkou, modelom a dátumom pridania, po 10 autách na stranu.
Admin má pri každom aute tlačidlá Upraviť a Zmazať a nad tabuľkou tlačidlo Pridať auto.
Vodič vidí tú istú tabuľku bez týchto tlačidiel.

![Formulár na pridanie auta](docs/screenshots/vehicle-form.png)

Pár vecí, ktoré nie sú na prvý pohľad vidieť:

- **ŠPZ sa ukladá v jednotnom tvare.** `ba 123-ab`, `BA 123 AB` aj `BA123AB` sú pre aplikáciu to isté
  auto, takže ho nejde zadať dvakrát.
- **Obnovenie stránky nikoho neodhlási.** Prihlásenie platí 30 minút (dá sa zmeniť v `.env`). Keď vyprší, aplikácia
  používateľa pri ďalšej akcii vráti na prihlasovaciu stránku.
- **Heslá sa nedajú hádať donekonečna.** Po 10 neúspešných pokusoch z jednej IP adresy
  sa z nej 15 minút nedá prihlásiť.
- **Heslá sa neukladajú.** V databáze je len ich hash (Argon2), z ktorého sa pôvodné heslo nedá získať.

Nových používateľov zatiaľ admin vytvára cez API, v aplikácii na to ešte nie je obrazovka
(postup je nižšie v časti [Pridanie vodiča](#pridanie-vodiča)).

## Ako je to postavené

Aplikácia má dve samostatné časti, ktoré spolu komunikujú cez HTTP:

- **Backend (API)** v Pythone s frameworkom FastAPI. Dáta ukladá do PostgreSQL cez SQLAlchemy,
  zmeny databázy riadi cez migrácie v Alembicu.
- **Frontend** v Reacte a TypeScripte, postavený cez Vite.

Všetko beží v Dockeri: databáza, API a webový server s frontendom sú tri kontajnery,
ktoré spustí jeden príkaz. Testy backendu sa po každom pushi do `main` a pri každom pull requeste
spúšťajú v GitHub Actions.

```mermaid
flowchart LR
    W["Webový server<br>port 5173"] -. "pošle aplikáciu" .-> F["Aplikácia<br>v prehliadači"]
    F -- "požiadavky s tokenom" --> A["API<br>port 8000"]
    A -- "číta a zapisuje" --> D[("Databáza")]
```

Webový server pošle prehliadaču aplikáciu len raz, pri otvorení stránky. Potom už aplikácia
komunikuje iba s API: pýta si autá, posiela zmeny a dostáva späť dáta.

### Prihlásenie

```mermaid
sequenceDiagram
    actor U as Používateľ
    participant F as Aplikácia
    participant A as API
    participant D as Databáza

    U->>F: zadá e-mail a heslo
    F->>A: pošle prihlasovacie údaje
    A->>D: nájde používateľa
    A->>A: overí heslo
    A-->>F: vráti token
    F->>F: uloží si token
    F->>A: kto som?
    A-->>F: e-mail a rola
    F->>A: daj prvých 10 áut
    A-->>F: zoznam áut
```

Token je podpísaný „preukaz“, ktorý aplikácia od tej chvíle posiela pri každej požiadavke.
API podľa neho spozná, kto sa pýta, a nemusí si pamätať žiadne prihlásenia.

### Kto čo smie

```mermaid
flowchart TD
    R["Požiadavka na autá"] --> T{"Je používateľ<br>prihlásený?"}
    T -- nie --> E1["Odmietnuté<br>aplikácia ho odhlási"]
    T -- áno --> W{"Chce niečo<br>zmeniť?"}
    W -- nie --> OK["Dostane zoznam áut"]
    W -- áno --> AD{"Je to admin?"}
    AD -- nie --> E2["Odmietnuté<br>nemá oprávnenie"]
    AD -- áno --> OK2["Zmena sa uloží"]
```

Skrytie tlačidiel vo frontende je len pohodlie pre vodiča. Skutočnú kontrolu robí backend,
takže vodič auto nezmaže ani vtedy, keď pošle požiadavku priamo na API. V kóde sú to dve funkcie
v [`backend/app/api/deps.py`](backend/app/api/deps.py): `get_current_user` zistí, kto požiadavku
posiela (inak `401`), a `require_admin` overí, či je to admin (inak `403`).

### Databáza

| Tabuľka | Čo obsahuje |
|---|---|
| `users` | e-mail (každý len raz), hash hesla, rola (`admin` alebo `driver`), dátum vytvorenia |
| `vehicles` | značka, model, ŠPZ (každá len raz), dátum pridania |

Tabuľky zatiaľ nie sú prepojené, autá nie sú priradené konkrétnemu vodičovi.

## Spustenie

Potrebuješ len [Docker Desktop](https://www.docker.com/products/docker-desktop/) (musí byť zapnutý)
a [Git](https://git-scm.com/). Python ani Node.js inštalovať netreba, všetko beží v kontajneroch.

### 1. Stiahni projekt

```bash
git clone https://github.com/Matus1232/car-fleet-.git
```

Ďalšie príkazy spúšťaj v priečinku projektu (`cd car-fleet-`).

### 2. Vytvor súbor `.env`

V priečinku projektu vytvor súbor s názvom presne `.env` (pozor, aby z neho Poznámkový blok
nespravil `.env.txt`) s týmto obsahom:

```
POSTGRES_USER=carfleet
POSTGRES_PASSWORD=change-me
POSTGRES_DB=carfleet
CORS_ORIGINS=http://localhost:5173
SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

| Premenná | Načo je |
|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | používateľ, heslo a názov databázy, ktorá sa vytvorí pri prvom spustení |
| `CORS_ORIGINS` | adresa, z ktorej smie prehliadač volať API; bez nej prehliadač požiadavky zablokuje |
| `SECRET_KEY` | tajný kľúč na podpisovanie tokenov, aspoň 32 znakov |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ako dlho platí prihlásenie |

Súbor obsahuje heslá, preto je v `.gitignore` a do Gitu sa nedostane.

### 3. Vygeneruj tajný kľúč

```bash
docker run --rm python:3.12-slim python -c "import secrets; print(secrets.token_hex(32))"
```

Docker si pri prvom spustení stiahne obraz s Pythonom a potom vypíše 64 náhodných znakov. Skopíruj ich do `.env` za `SECRET_KEY=`. Bez kľúča sa aplikácia
nespustí. Docker vtedy vypíše chybu `SECRET_KEY must be set in .env`.

### 4. Spusti aplikáciu

```bash
docker compose up --build
```

Prvé spustenie trvá pár minút, lebo Docker sťahuje a zostavuje všetky kontajnery. Aplikácia je pripravená,
keď sa vo výpise objaví `Application startup complete`. Databázové tabuľky sa vytvoria automaticky.

| Adresa | Čo tam je |
|---|---|
| http://localhost:5173 | aplikácia |
| http://localhost:8000/docs | dokumentácia API, dá sa v nej API aj priamo skúšať |
| http://localhost:8000/health | rýchla kontrola, či beží API a databáza |

### 5. Vytvor prvého admina

Databáza je na začiatku prázdna a nikto sa nevie prihlásiť. Prvého admina preto vytvoríš z terminálu.
Otvor druhý terminál (prvý drží bežiacu aplikáciu) a v priečinku projektu spusti:

```bash
docker compose exec api python -m app.cli create-admin --email admin@firma.sk
```

Príkaz sa dvakrát spýta na heslo (aspoň 8 znakov, pri písaní ho neuvidíš). Potom sa prihlás
na http://localhost:5173.

### Pridanie vodiča

1. Otvor http://localhost:8000/docs a vpravo hore klikni na **Authorize**.
2. Do `username` zadaj e-mail admina, do `password` jeho heslo a potvrď.
3. Rozbaľ **POST /users**, klikni na **Try it out**, vlož údaje a klikni na **Execute**:

```json
{ "email": "vodic@firma.sk", "password": "heslo1234", "role": "driver" }
```

Ak namiesto `driver` napíšeš `admin`, vytvoríš ďalšieho admina.

### Zastavenie

Aplikáciu zastavíš klávesmi `Ctrl+C` v termináli, kde beží, alebo príkazom `docker compose down`.
Dáta v databáze ostanú uložené aj po zastavení. Ak ich chceš úplne zmazať a začať odznova,
použi `docker compose down -v`.

### Vývojový a produkčný režim

Príkaz `docker compose up` spúšťa vývojový režim. Docker k nemu automaticky načíta
`docker-compose.override.yml`. Zmeny v kóde sa hneď prejavia: frontend sa obnoví v prehliadači
a API sa samo reštartuje.

Príkaz `docker compose -f docker-compose.yml up -d` spustí aplikáciu tak, ako by bežala na serveri.
Frontend sa vopred zostaví do hotových súborov, ktoré posiela nginx, API beží bez automatického
reštartu a dokumentácia na `/docs` je vypnutá.

## Testy

Backend má testy v priečinku `backend/tests`. Bežia mimo Dockeru, takže na ne treba
[Python](https://www.python.org/downloads/) 3.12 alebo novší. Testy pri každom spustení mažú tabuľky, preto
používajú vlastnú databázu, aby sa nezmazali dáta z aplikácie.

Testovaciu databázu vytvoríš raz, keď aplikácia beží:

```bash
docker compose exec db psql -U carfleet -d postgres -c "CREATE DATABASE carfleet_test"
```

Potom v priečinku `backend` nainštaluj knižnice:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

Testy spustíš v PowerShelli takto:

```powershell
$env:TEST_DATABASE_URL="postgresql+psycopg://carfleet:change-me@127.0.0.1:5432/carfleet_test"; pytest
```

V Git Bash, na Linuxe alebo na Macu takto:

```bash
TEST_DATABASE_URL=postgresql+psycopg://carfleet:change-me@127.0.0.1:5432/carfleet_test pytest
```

Ak máš v `.env` iné meno alebo heslo k databáze, uprav ich aj v týchto príkazoch. Adresa je
zámerne `127.0.0.1` a nie `localhost`. Na Windows sa `localhost` najprv skúša cez IPv6, a to
každé pripojenie k databáze spomalí natoľko, že testy bežia minúty namiesto sekúnd.

GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) pri každom pushi do `main`
a pri každom pull requeste spustí kontrolu kódu (ruff), testy a kontrolu migrácií a zostaví Docker
image backendu. Frontend v CI zatiaľ nie je.

## Frontend bez Dockeru

Pri práci na frontende ho môžeš spustiť aj priamo cez [Node.js](https://nodejs.org) (verzia LTS).
Databáza a API pritom ďalej bežia v Dockeri. Najprv zastav kontajner s frontendom, lebo obsadzuje
port 5173:

```bash
docker compose stop web
```

Potom v priečinku `frontend`:

| Príkaz | Čo robí |
|---|---|
| `npm install` | nainštaluje knižnice (prvýkrát a po zmene `package.json`) |
| `npm run dev` | spustí vývojový server, zmeny v kóde sa hneď prejavia v prehliadači |
| `npm run build` | skontroluje typy a zostaví hotovú verziu do `dist/` |
| `npm run lint` | skontroluje kód (oxlint) |

Adresa API je napevno v [`frontend/src/api.ts`](frontend/src/api.ts) (`http://localhost:8000`).
Popis jednotlivých súborov frontendu je vo [frontend/README.md](frontend/README.md).

## Štruktúra projektu

```
backend/                     API: endpointy, databázové modely, migrácie, testy
frontend/                    React aplikácia
docs/                        screenshoty pre README
.github/                     CI a automatické aktualizácie knižníc (Dependabot)
docker-compose.yml           databáza, API a frontend
docker-compose.override.yml  vývojové nastavenie, Docker ho načíta automaticky
```

## Stav projektu

- [x] Docker Compose, PostgreSQL, databázové migrácie
- [x] API na správu áut
- [x] Prihlásenie, roly a ochrana proti hádaniu hesiel
- [x] Testy a CI pre backend
- [x] Frontend: prihlásenie, zoznam áut, pridanie, úprava, mazanie
- [ ] Servisná história áut
- [ ] Pripomienky termínov (STK, emisná kontrola, poistenie, diaľničná známka)
