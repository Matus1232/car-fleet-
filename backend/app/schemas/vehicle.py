import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

LICENSE_PLATE_MAX_LENGTH = 20
LICENSE_PLATE_RE = re.compile(r"[A-Z0-9]+")


def normalize_license_plate(value: str) -> str:
    """'ba 123 ab' aj 'BA-123AB' -> 'BA123AB', aby sa jedno auto nedalo zadať viackrát."""
    plate = re.sub(r"[\s-]+", "", value).upper()
    if not LICENSE_PLATE_RE.fullmatch(plate):
        raise ValueError(
            "License plate must contain only letters and digits (spaces and hyphens are ignored)"
        )
    # Dĺžku kontrolujeme až po normalizácii: 'BA 123 AB' má 9 znakov, ale uloží sa ich 7.
    if len(plate) > LICENSE_PLATE_MAX_LENGTH:
        raise ValueError(f"License plate must have at most {LICENSE_PLATE_MAX_LENGTH} characters")
    return plate


class VehicleBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    brand: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=50)
    license_plate: str

    @field_validator("license_plate")
    @classmethod
    def _normalize_plate(cls, value: str) -> str:
        return normalize_license_plate(value)


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(VehicleBase):
    """Všetky polia sú voliteľné, ale ak sú poslané, nesmú byť null."""

    brand: str = Field(default=None, min_length=1, max_length=50)
    model: str = Field(default=None, min_length=1, max_length=50)
    license_plate: str = None

    @field_validator("brand", "model", "license_plate", mode="before")
    @classmethod
    def _not_null(cls, value):
        if value is None:
            raise ValueError("Field cannot be null")
        return value


class VehicleRead(BaseModel):
    """Výstup sa nevaliduje: čo je už v databáze, to sa len vypíše (aj staršie dáta)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    brand: str
    model: str
    license_plate: str
    created_at: datetime


class VehiclePage(BaseModel):
    items: list[VehicleRead]
    total: int
    skip: int
    limit: int
