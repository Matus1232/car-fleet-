from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ServiceRecord(Base):
    """Jeden servisný záznam auta: čo sa robilo, kedy a koľko to stálo."""

    __tablename__ = "service_records"
    # Poistka priamo v databáze: záporná cena sa neuloží, ani keby ju niekto zapísal mimo API.
    __table_args__ = (CheckConstraint("cost >= 0", name="service_records_cost_check"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # Cudzí kľúč: záznam patrí práve jednému autu. ondelete="CASCADE" znamená, že keď sa auto
    # zmaže, databáza sama zmaže aj jeho servisné záznamy. Index zrýchli hľadanie podľa auta.
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), index=True
    )
    description: Mapped[str] = mapped_column(String(500))
    # Peniaze nikdy nie ako float (0.1 + 0.2 != 0.3). Numeric(10, 2) = najviac 10 číslic,
    # z toho 2 za desatinnou čiarkou, teda do 99 999 999,99. V Pythone tomu zodpovedá Decimal.
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # Kedy bol servis (len deň, bez času). Zadáva ho používateľ, nemusí to byť dnešok.
    service_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
