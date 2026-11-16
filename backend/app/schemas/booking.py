from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.booking import FIRST_HOUR, LAST_HOUR


class BookingCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    booking_date: date
    # Hodina začiatku termínu: 10 znamená 10:00 až 11:00. Hranice sú otváracie hodiny servisu.
    hour: int = Field(ge=FIRST_HOUR, le=LAST_HOUR)
    note: str | None = Field(default=None, max_length=200)

    @field_validator("note")
    @classmethod
    def _empty_note_is_none(cls, value: str | None) -> str | None:
        # Prázdne pole z formulára ("" alebo samé medzery) uložíme ako NULL, nie ako prázdny text.
        return value or None


class BookingRead(BaseModel):
    """Jeden obsadený termín tak, ako ho smie vidieť ten, kto sa pýta.

    Kalendár musí každému ukázať, ktoré termíny sú obsadené. Kto si ich rezervoval a čo
    napísal do poznámky, je však vec toho človeka: user_email a note sú vyplnené len pri
    vlastnej rezervácii alebo keď sa pýta admin, inak sú null.
    """

    id: int
    booking_date: date
    hour: int
    mine: bool  # je to rezervácia toho, kto sa pýta?
    user_email: str | None
    note: str | None
