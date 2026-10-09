from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def _get_or_404(db: Session, vehicle_id: int) -> Vehicle:
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vozidlo neexistuje")
    return vehicle


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Vozidlo s touto ŠPZ už existuje"
        )


@router.get("", response_model=list[VehicleRead])
def list_vehicles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.scalars(select(Vehicle).order_by(Vehicle.id).offset(skip).limit(limit)).all()


@router.get("/{vehicle_id}", response_model=VehicleRead)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, vehicle_id)


@router.post("", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
def create_vehicle(data: VehicleCreate, db: Session = Depends(get_db)):
    vehicle = Vehicle(**data.model_dump())
    db.add(vehicle)
    _commit(db)
    db.refresh(vehicle)
    return vehicle


@router.patch("/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(vehicle_id: int, data: VehicleUpdate, db: Session = Depends(get_db)):
    vehicle = _get_or_404(db, vehicle_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(vehicle, field, value)
    _commit(db)
    db.refresh(vehicle)
    return vehicle


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = _get_or_404(db, vehicle_id)
    db.delete(vehicle)
    db.commit()
