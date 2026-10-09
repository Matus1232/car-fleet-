from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VehicleBase(BaseModel):
    brand: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=50)
    license_plate: str = Field(min_length=1, max_length=20)


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    brand: str | None = Field(default=None, min_length=1, max_length=50)
    model: str | None = Field(default=None, min_length=1, max_length=50)
    license_plate: str | None = Field(default=None, min_length=1, max_length=20)


class VehicleRead(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
