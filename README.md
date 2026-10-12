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

```

Vo Windows PowerShelli sa premenná nastavuje inak:

## Stav projektu

- [x] Štruktúra projektu, Docker Compose, PostgreSQL
- [x] Databázový model a migrácie
- [x] CRUD endpointy pre vozidlá
- [ ] Autentifikácia
- [x] Testy a CI
- [ ] Frontend
- [ ] Deployment
