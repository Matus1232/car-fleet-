from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api import auth, users, vehicles
from app.core.config import settings
from app.db.session import get_db

app = FastAPI(
    title=settings.app_name,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(vehicles.router)


@app.get("/health")  # zámerne verejný: monitoring sa nemusí prihlasovať
def health(db: Session = Depends(get_db)):
    """Overí, že API beží a vie sa spojiť s databázou."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database is unavailable") from exc
    return {"status": "ok", "database": "connected"}
