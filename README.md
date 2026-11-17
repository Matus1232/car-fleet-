# Car Fleet Manager

**Slovenčina** | [English](README.en.md)

Webová aplikácia na správu firemných áut a rezerváciu termínov servisu.

**Naživo:** https://fearless-rebirth-production-132141c8.up.railway.app

## Čo aplikácia vie

- **Registrácia a prihlásenie.** Účet si vytvorí každý sám. Admin vzniká len príkazom na serveri.
- **Termín servisu.** Kalendár mesiaca, po kliknutí na deň hodinové termíny od 8:00 do 17:00.
  Jeden termín sa nedá rezervovať dvakrát.
- **Rezervácie pre admina.** Admin vidí, kto a kedy príde, aj s poznámkou, a môže rezervácie rušiť.
- **Vozový park (len admin).** Autá s platnosťou STK, servisná história s cenami, prehľad áut
  s končiacou alebo neplatnou STK.
- **Cenník** servisných úkonov a **e-shop** (pripravuje sa).

## Architektúra

```mermaid
flowchart LR
    U["Prehliadač"] -- "HTTPS" --> R["Railway<br>(TLS, skutočná IP)"]
    R --> N["nginx<br>React aplikácia"]
    N -- "/api" --> A["FastAPI<br>backend"]
    A --> D[("PostgreSQL")]

    subgraph S["súkromná sieť Railway"]
        A
        D
    end
```

Verejne dostupný je len frontend. nginx posiela prehliadaču React aplikáciu a požiadavky
na `/api` posiela ďalej na backend. Backend ani databáza nemajú verejnú adresu.

## Databáza

```mermaid
erDiagram
    users ||--o{ bookings : "rezervuje"
    vehicles ||--o{ service_records : "má"

    users {
        int id PK
        string email UK
        string hashed_password "Argon2 hash"
        string role "admin alebo driver"
        datetime created_at
    }
    bookings {
        int id PK
        int user_id FK
        date booking_date "s hour spolu jedinečné"
        smallint hour "8 až 16"
        string note "nepovinné"
        datetime created_at
    }
    vehicles {
        int id PK
        string brand
        string model
        string license_plate UK "normalizovaná ŠPZ"
        date stk_valid_until "nepovinné"
        datetime created_at
    }
    service_records {
        int id PK
        int vehicle_id FK
        string description
        numeric cost "nie záporná"
        date service_date
        datetime created_at
    }
    revoked_tokens {
        string jti PK "ID odhláseného tokenu"
        datetime expires_at
    }
    rate_limit_hits {
        int id PK
        string scope "login alebo register"
        string key "IP adresa"
        datetime created_at
    }
```

- Používateľ môže mať veľa rezervácií, auto veľa servisných záznamov. Keď sa zmaže používateľ
  alebo auto, databáza zmaže aj jeho rezervácie či záznamy (`ON DELETE CASCADE`).
- Dvojica deň a hodina je jedinečná (`UNIQUE`). Stráži to databáza, takže termín sa nedá
  rezervovať dvakrát ani vtedy, keď dvaja ľudia kliknú naraz.
- `revoked_tokens` a `rate_limit_hits` nesúvisia s ostatnými tabuľkami. Slúžia na odhlásenie
  a na limit pokusov o prihlásenie a registráciu.

## Technológie

| Časť | Čo je použité |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, Alembic (migrácie), PostgreSQL |
| Frontend | React, TypeScript, Vite, React Router, obyčajné CSS |
| Prevádzka | Docker, nginx, Railway, GitHub Actions (testy a kontrola kódu pri každom pushi) |

## Bezpečnosť

- Heslá sú uložené len ako hash (Argon2).
- Token (JWT) je v **httpOnly cookie**, ktorú JavaScript na stránke neprečíta. Cookie je `Secure`
  a `SameSite=Strict`, zmeny navyše vyžadujú hlavičku proti CSRF.
- **Odhlásenie** token zruší okamžite, nie až keď vyprší.
- Hádanie hesiel a hromadná registrácia majú **limit na IP adresu**. Pokusy sú v databáze,
  takže limit platí aj po reštarte.
- Oprávnenia kontroluje backend (`401` neprihlásený, `403` bez oprávnenia), nie len skryté tlačidlá.
- nginx vynúti HTTPS a posiela bezpečnostné hlavičky (HSTS, Content-Security-Policy).

## Štruktúra

```
backend/    API: endpointy, databázové modely, migrácie, testy
frontend/   React aplikácia a nginx
```
