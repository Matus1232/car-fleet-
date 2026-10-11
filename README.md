# Car Fleet Manager

Webová aplikácia na správu vozového parku: autá, servisná história a dôležité termíny (STK, EK, poistenie, dialničná známka).

**Tech stack:** Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, React, Docker, GitHub Actions

## Spustenie

```bash
cp .env.example .env
docker compose up --build
```

Migrácie databázy (`alembic upgrade head`) sa spustia automaticky pri štarte API.
`docker-compose.override.yml` (live reload, `ENVIRONMENT=development` z `.env`) sa načíta sám;
produkčný beh: `docker compose -f docker-compose.yml up -d`.

- API: http://localhost:8000
- Swagger dokumentácia: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Stav projektu

- [x] Štruktúra projektu, Docker Compose, PostgreSQL
- [x] Databázový model a migrácie
- [x] CRUD endpointy pre vozidlá
- [ ] Autentifikácia
- [ ] Testy a CI
- [ ] Frontend
- [ ] Deployment
