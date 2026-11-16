from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Servis berie autá každú celú hodinu od 8:00 do 16:00 (posledný termín končí o 17:00).
# Tie isté čísla má frontend v src/slots.ts, treba ich meniť spolu.
FIRST_HOUR = 8
LAST_HOUR = 16

# Názov unique constraintu na dvojici (deň, hodina). Podľa neho API spozná obsadený termín.
SLOT_UNIQUE = "bookings_slot_key"


class Booking(Base):
    """Rezervácia termínu servisu: kto príde, v ktorý deň a o ktorej hodine."""

    __tablename__ = "bookings"
    __table_args__ = (
        # Jeden termín (deň + hodina) smie mať len jednu rezerváciu a stráži to databáza.
        # Kontrola v Pythone ("je voľné? tak zapíš") by nestačila: keď dvaja ľudia kliknú
        # naraz, obaja uvidia voľný termín a obaja zapíšu. Databáza druhý zápis odmietne.
        UniqueConstraint("booking_date", "hour", name=SLOT_UNIQUE),
        # Poistka: hodina mimo otváracích hodín sa neuloží, ani keby ju niekto zapísal mimo API.
        CheckConstraint(f"hour BETWEEN {FIRST_HOUR} AND {LAST_HOUR}", name="bookings_hour_check"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Kto si termín rezervoval. Keď sa používateľ zmaže, zmažú sa aj jeho rezervácie.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # Deň a hodina sú dva stĺpce, nie jeden čas: termín je vždy celá hodina, takže stačí
    # malé číslo (8 až 16) a nemusíme riešiť minúty ani časové pásma.
    booking_date: Mapped[date] = mapped_column(Date)
    hour: Mapped[int] = mapped_column(SmallInteger)
    # Nepovinná poznámka pre servis, napr. o ktoré auto ide a čo treba spraviť.
    note: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
