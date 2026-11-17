from datetime import datetime

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RateLimitHit(Base):
    """Jeden započítaný pokus (napr. neúspešné prihlásenie) z jednej IP adresy.

    Pokusy sú v databáze, nie v pamäti procesu: neztratia sa po reštarte aplikácie
    a vidia ich všetky procesy naraz, aj keď ich beží viac.
    """

    __tablename__ = "rate_limit_hits"
    # Index presne na to, čo hľadáme: pokusy jedného druhu (scope) z jednej IP za posledný čas.
    __table_args__ = (Index("ix_rate_limit_hits_lookup", "scope", "key", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    scope: Mapped[str] = mapped_column(String(20))  # "login" alebo "register"
    key: Mapped[str] = mapped_column(String(64))  # IP adresa
    # Čas zadáva aplikácia (nie databáza), aby ho testy vedeli posúvať bez čakania.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
