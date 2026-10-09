from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import vehicles
from app.core.config import settings
from app.db.session import get_db

app = FastAPI(title=settings.app_name)
app.include_router(vehicles.router)


@app.get("/")
def root():
    return {"message": settings.app_name}


@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Overí, že API beží a vie sa spojiť s databázou."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
