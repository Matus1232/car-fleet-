import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

LICENSE_PLATE_RE = re.compile(r"[A-Z0-9-]+")


def normalize_license_plate(value: str) -> str:
    """'ba 123 ab' -> 'BA123AB', aby sa jedno auto nedalo zadať viackrát."""
    plate = re.sub(r"\s+", "", value).upper()
    if not LICENSE_PLATE_RE.fullmatch(plate):
        raise ValueError("License plate may contain only letters, digits and hyphens")
    return plate


class VehicleBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    brand: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=50)
    license_plate: str = Field(min_length=1, max_length=20)

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
    license_plate: str = Field(default=None, min_length=1, max_length=20)

    @field_validator("brand", "model", "license_plate", mode="before")
    @classmethod
    def _not_null(cls, value):
        if value is None:
            raise ValueError("Field cannot be null")
        return value


class VehicleRead(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class VehiclePage(BaseModel):
    items: list[VehicleRead]
    total: int
    skip: int
    limit: int
