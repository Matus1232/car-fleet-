from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.vehicle import LICENSE_PLATE_UNIQUE, Vehicle
from app.schemas.vehicle import VehicleCreate, VehiclePage, VehicleRead, VehicleUpdate

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def _get_or_404(db: Session, vehicle_id: int) -> Vehicle:
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")
    return vehicle


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        diag = getattr(exc.orig, "diag", None)
        if getattr(diag, "constraint_name", None) == LICENSE_PLATE_UNIQUE:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "A vehicle with this license plate already exists",
            ) from exc
        raise


@router.get("", response_model=VehiclePage)
def list_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items = db.scalars(select(Vehicle).order_by(Vehicle.id).offset(skip).limit(limit)).all()
    total = db.scalar(select(func.count()).select_from(Vehicle))
    return VehiclePage(items=items, total=total, skip=skip, limit=limit)


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
    result = db.execute(delete(Vehicle).where(Vehicle.id == vehicle_id))
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")
