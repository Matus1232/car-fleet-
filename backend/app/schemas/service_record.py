from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ServiceRecordCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    description: str = Field(min_length=1, max_length=500)
    # Rovnaké hranice ako stĺpec Numeric(10, 2) v databáze: najviac 10 číslic, 2 desatinné miesta.
    cost: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    service_date: date


class ServiceRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int
    description: str
    # Decimal sa do JSON zapíše ako text ("120.50"), aby sa cestou nestratila presnosť.
    cost: Decimal
    service_date: date
    created_at: datetime
