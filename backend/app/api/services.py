from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.api.vehicles import PG_INT_MAX
from app.db.session import get_db
from app.models.service_record import ServiceRecord
from app.models.vehicle import Vehicle
from app.schemas.service_record import ServiceRecordCreate, ServiceRecordRead

# Servisné záznamy sú "vnorené" pod autom: /vehicles/5/services = servis auta s id 5.
# Rovnaké pravidlá ako pri autách: čítať smie každý prihlásený, zapisovať len admin.
router = APIRouter(
    prefix="/vehicles/{vehicle_id}/services",
    tags=["services"],
    dependencies=[Depends(get_current_user)],
)
admin_only = [Depends(require_admin)]


def _vehicle_not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")


@router.get("", response_model=list[ServiceRecordRead])
def list_services(vehicle_id: int = Path(ge=1, le=PG_INT_MAX), db: Session = Depends(get_db)):
    # Bez tejto kontroly by neexistujúce auto vrátilo prázdny zoznam namiesto 404.
    if db.get(Vehicle, vehicle_id) is None:
        raise _vehicle_not_found()
    # Najnovší servis hore. Pri rovnakom dátume rozhodne id, aby bolo poradie vždy rovnaké.
    return db.scalars(
        select(ServiceRecord)
        .where(ServiceRecord.vehicle_id == vehicle_id)
        .order_by(ServiceRecord.service_date.desc(), ServiceRecord.id.desc())
    ).all()


@router.post(
    "",
    response_model=ServiceRecordRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=admin_only,
)
def create_service(
    data: ServiceRecordCreate,
    vehicle_id: int = Path(ge=1, le=PG_INT_MAX),
    db: Session = Depends(get_db),
):
    if db.get(Vehicle, vehicle_id) is None:
        raise _vehicle_not_found()
    record = ServiceRecord(vehicle_id=vehicle_id, **data.model_dump())
    db.add(record)
    try:
        db.commit()
    except IntegrityError as exc:
        # Auto niekto zmazal presne medzi našou kontrolou a uložením: cudzí kľúč zápis odmietne.
        db.rollback()
        raise _vehicle_not_found() from exc
    db.refresh(record)
    return record


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=admin_only)
def delete_service(
    vehicle_id: int = Path(ge=1, le=PG_INT_MAX),
    service_id: int = Path(ge=1, le=PG_INT_MAX),
    db: Session = Depends(get_db),
):
    # Podmienka na vehicle_id: cez /vehicles/1/services/7 sa nedá zmazať záznam iného auta.
    result = db.execute(
        delete(ServiceRecord).where(
            ServiceRecord.id == service_id, ServiceRecord.vehicle_id == vehicle_id
        )
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Service record not found")
