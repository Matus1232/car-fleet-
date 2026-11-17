# Car Fleet Manager

**Slovenčina** | [English](README.en.md)

Webová aplikácia na správu firemných áut. Firma v nej vidí, aké autá má, a môže ich pridávať,
upravovať a mazať.

Používatelia majú dve roly. **Admin** spravuje autá a vidí všetky rezervácie servisu. **Vodič**
si môže len rezervovať termín servisu, vozový park nevidí. Účet vodiča si vytvorí každý sám
registráciou, admin vzniká len príkazom v termináli.

Ku každému autu sa dá viesť servisná história: čo sa robilo, kedy a koľko to stálo.

Termín servisu si vodič vyberie v kalendári: klikne na deň a rezervuje si voľnú hodinu.
Admin vidí, kto a kedy príde.

Toto je prvá verzia (MVP). Pri aute sa zatiaľ sleduje platnosť STK, neskôr pribudnú ďalšie termíny:
emisná kontrola, poistenie a diaľničná známka.

![Zoznam áut v aplikácii](docs/screenshots/vehicles-admin.png)

## Čo aplikácia vie

Po prihlásení sa zobrazí úvodná stránka s menu. Admin v ňom má **Vozový park** a **Rezervácie servisu**,
vodič **Termín servisu**. Obaja vidia aj **Cenník** servisných úkonov a **E-shop**, ktorý sa zatiaľ len
pripravuje.

### Vozový park (len admin)

Hore je prehľad: koľko áut firma má, koľkým končí STK do 30 dní a koľké sú už po STK.

Pod ním je zoznam áut s ŠPZ, značkou, modelom, platnosťou STK a dátumom pridania, po 10 autách na stranu.
Pri aute, ktorému STK končí alebo už neplatí, je pri dátume štítok. Dátum STK je nepovinný.
Pri každom aute sú tlačidlá Upraviť a Zmazať a nad tabuľkou tlačidlo Pridať auto.

Tlačidlo Servis pri aute otvorí jeho servisné záznamy (dátum, čo sa robilo, cena) aj so súčtom,
koľko servis auta stál dokopy. Záznamy sa dajú pridávať aj mazať.

Vodič túto časť nevidí vôbec: nemá ju v menu a API mu na autá aj servis odpovie `403`.
Registrácia je verejná, takže účet si môže založiť ktokoľvek, a firemné autá mu ukazovať nechceme.

![Formulár na pridanie auta](docs/screenshots/vehicle-form.png)

### Termín servisu

Stránka ukáže kalendár celého mesiaca. Pri každom pracovnom dni je počet voľných termínov.
Po kliknutí na deň sa zobrazia jeho hodinové termíny od 8:00 do 17:00, každý vo vlastnom farebnom
rámčeku. Voľný termín sa dá rezervovať a pripísať k nemu poznámku pre servis, napríklad o ktoré auto ide.
Rezervovať sa dá od pondelka do piatka, najviac 60 dní dopredu.

Pod kalendárom má vodič zoznam svojich rezervácií a môže ich zrušiť. Cudzie termíny vidí len ako
obsadené. Admin vidí v kalendári aj v zozname rezervácie všetkých ľudí s e-mailom a poznámkou
a môže zrušiť hocktorú.

### Cenník a e-shop

Cenník ukazuje orientačné ceny bežných úkonov (výmena oleja, diagnostika, prezutie, ...) s odkazom
na rezerváciu termínu. Ceny sú napevno vo frontende, v
[`PriceListPage.tsx`](frontend/src/components/PriceListPage.tsx). E-shop zatiaľ len oznamuje,
že sa pripravuje.

Pár vecí, ktoré nie sú na prvý pohľad vidieť:

- **ŠPZ sa ukladá v jednotnom tvare.** `ba 123-ab`, `BA 123 AB` aj `BA123AB` sú pre aplikáciu to isté
  auto, takže ho nejde zadať dvakrát.
- **Obnovenie stránky nikoho neodhlási.** Prihlásenie platí 30 minút (dá sa zmeniť v `.env`). Keď vyprší, aplikácia
  používateľa pri ďalšej akcii vráti na prihlasovaciu stránku.
- **Token neukradne ani podstrčený skript.** Prehliadač ho drží v httpOnly cookie, ktorú JavaScript
  na stránke nevidí. Bližšie v časti [Prihlásenie](#prihlásenie).
- **Odhlásenie platí hneď.** Odhlásený token prestane fungovať okamžite, aj keby si ho niekto skopíroval.
- **Heslá sa nedajú hádať donekonečna.** Po 10 neúspešných pokusoch z jednej IP adresy
  sa z nej 15 minút nedá prihlásiť. Pokusy sú v databáze, takže ich nevynuluje ani reštart aplikácie.
- **Heslá sa neukladajú.** V databáze je len ich hash (Argon2), z ktorého sa pôvodné heslo nedá získať.
- **Registráciou nevznikne admin.** Rolu si človek nevyberá, nový účet je vždy vodič. Z jednej IP adresy
  sa dá založiť najviac 10 účtov za hodinu.
- **Jeden termín nejde rezervovať dvakrát.** Stráži to priamo databáza, takže keď dvaja ľudia kliknú
  na ten istý termín naraz, uspeje len jeden.

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
    F["Aplikácia<br>v prehliadači"] -- "stránka aj /api" --> W["Webový server<br>port 5173"]
    W -- "/api" --> A["API<br>port 8000"]
    A -- "číta a zapisuje" --> D[("Databáza")]
```

Prehliadač komunikuje len s jednou adresou. Webový server mu pošle aplikáciu a požiadavky
na `/api/...` posiela ďalej na API (`/api/vehicles` → `/vehicles`). Pri vývoji to robí Vite,
v produkcii nginx. Na API sa tak zvonka nedá dostať priamo a cookie s tokenom môže byť čo najprísnejšia.

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
    A-->>F: token v httpOnly cookie
    F->>A: kto som? (prehliadač pripojí cookie sám)
    A-->>F: e-mail a rola
    F->>A: daj prvých 10 áut
    A-->>F: zoznam áut
```

Token je podpísaný „preukaz“ (JWT). API podľa neho spozná, kto sa pýta, a nemusí si pamätať
žiadne prihlásenia. Kde token leží a ako sa ruší:

| Čo | Ako | Prečo |
|---|---|---|
| Token je v **httpOnly cookie** | JavaScript ju neprečíta, prehliadač ju pripojí sám | keby sa do stránky dostal cudzí skript (XSS), token neukradne |
| Cookie má **SameSite=Strict** a **Secure** | prehliadač ju pošle len našej stránke a len cez HTTPS | cudzia stránka ju nepoužije a cestou sa nedá odpočúvať |
| Pri zmenách cez cookie musí prísť hlavička **`X-Requested-With`** | náš frontend ju posiela vždy, cudzí formulár ju pridať nevie | druhá poistka proti CSRF (cudzia stránka odošle požiadavku v tvojom mene) |
| **Odhlásenie** zapíše ID tokenu do tabuľky `revoked_tokens` | API taký token už neprijme | odhlásenie platí hneď, nie až keď token o 30 minút vyprší |
| Prísna **Content-Security-Policy** z nginx | prehliadač spustí len skripty z našej adresy | ďalšia ochrana proti XSS |

Swagger (`/docs`) a testy posielajú token po starom, v hlavičke `Authorization: Bearer`. Tú prehliadač
nikdy nepridá sám, preto pri nej kontrola `X-Requested-With` netreba.

### Kto čo smie

```mermaid
flowchart TD
    R["Požiadavka na autá"] --> T{"Je používateľ<br>prihlásený?"}
    T -- nie --> E1["Odmietnuté<br>aplikácia ho odhlási"]
    T -- áno --> AD{"Je to admin?"}
    AD -- nie --> E2["Odmietnuté<br>nemá oprávnenie"]
    AD -- áno --> OK["Dostane autá<br>alebo sa zmena uloží"]
```

Skrytie vozového parku vo frontende je len pohodlie pre vodiča. Skutočnú kontrolu robí backend,
takže vodič autá neuvidí ani vtedy, keď pošle požiadavku priamo na API. V kóde sú to dve funkcie
v [`backend/app/api/deps.py`](backend/app/api/deps.py): `get_current_user` zistí, kto požiadavku
posiela (inak `401`), a `require_admin` overí, či je to admin (inak `403`).

Pri rezerváciách je to trochu iné: rezervovať smie každý prihlásený, zrušiť len vlastnú rezerváciu
(admin hocktorú). Kto si termín rezervoval a čo k nemu napísal, pošle API len majiteľovi a adminovi.

### Databáza

| Tabuľka | Čo obsahuje |
|---|---|
| `users` | e-mail (každý len raz), hash hesla, rola (`admin` alebo `driver`), dátum vytvorenia |
| `vehicles` | značka, model, ŠPZ (každá len raz), platnosť STK (nepovinná), dátum pridania |
| `service_records` | ku ktorému autu patrí, čo sa robilo, cena, dátum servisu |
| `bookings` | kto si termín rezervoval, deň, hodina (dvojica deň a hodina len raz), poznámka |

Každý servisný záznam patrí jednému autu. Keď sa auto zmaže, zmažú sa aj jeho záznamy.
Rezervácia patrí jednému používateľovi a zmaže sa spolu s ním.
Autá zatiaľ nie sú priradené konkrétnemu vodičovi.

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
SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

| Premenná | Načo je |
|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | používateľ, heslo a názov databázy, ktorá sa vytvorí pri prvom spustení |
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

### Ďalší používatelia

Vodiči si účet vytvoria sami: na prihlasovacej stránke kliknú na **Zaregistruj sa**.

Účet vie založiť aj admin cez API, a len takto sa dá pridať ďalší admin:

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
reštartu a dokumentácia na `/docs` je vypnutá. Cookie s tokenom je v tomto režime len pre HTTPS
(`Secure`). Chrome a Firefox ju na `http://localhost` povolia, iné prehliadače nemusia.

## Nasadenie na Railway

Na [Railway](https://railway.com) vytvor v jednom projekte tri služby:

1. **PostgreSQL** z ponuky databáz.
2. **Backend**: z tohto repozitára, priečinok `backend`. Railway nájde `Dockerfile` sám.
3. **Frontend**: z tohto repozitára, priečinok `frontend`.

**Verejnú doménu (Generate Domain) daj len frontendu.** Backend musí byť dostupný iba cez súkromnú
sieť Railway. Inak by si ktokoľvek mohol poslať vymyslenú hlavičku `X-Real-IP` a obísť limit
na hádanie hesiel.

Premenné prostredia backendu:

| Premenná | Hodnota |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}`, Railway sem dosadí adresu databázy (aplikácia si ju sama upraví pre ovládač psycopg) |
| `SECRET_KEY` | nový náhodný kľúč (pozri [krok 3](#3-vygeneruj-tajný-kľúč)), nie ten z `.env` |
| `CLIENT_IP_HEADER` | `X-Real-IP`, v nej posiela Railway skutočnú IP návštevníka |

Premenná prostredia frontendu:

| Premenná | Hodnota |
|---|---|
| `API_UPSTREAM` | súkromná adresa backendu, napr. `http://backend.railway.internal:8000` (podľa názvu služby) |

`PORT` nastaví Railway sám. HTTPS rieši Railway: nginx presmeruje `http://` na `https://` a pošle
hlavičku HSTS, aby prehliadač nabudúce otváral stránku rovno cez HTTPS. Migrácie databázy sa spustia
pri každom štarte backendu. Prvého admina vytvoríš príkazom `python -m app.cli create-admin` v termináli
služby backend (Railway CLI: `railway ssh`).

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

Vite posiela požiadavky na `/api` na `http://localhost:8000` (nastavenie je vo
[`frontend/vite.config.ts`](frontend/vite.config.ts)). Ak spúšťaš aj backend mimo Dockeru, pridaj do `.env`
riadok `COOKIE_SECURE=false`, lebo lokálne nebeží HTTPS.
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
- [x] Token v httpOnly cookie, odhlásenie so zrušením tokenu, rate limiter v databáze
- [x] Príprava na nasadenie na Railway (nginx proxy, HTTPS, bezpečnostné hlavičky)
- [x] Testy a CI pre backend
- [x] Frontend: prihlásenie, zoznam áut, pridanie, úprava, mazanie
- [x] Servisná história áut s cenou
- [x] Prehľad: počet áut, končiaca a neplatná STK
- [x] Registrácia, úvodná stránka a rezervácia termínov servisu v kalendári
- [x] Cenník servisných úkonov
- [ ] E-shop
- [ ] Ďalšie termíny (emisná kontrola, poistenie, diaľničná známka)
