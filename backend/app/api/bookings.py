from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.vehicles import PG_INT_MAX
from app.db.session import get_db
from app.models.booking import SLOT_UNIQUE, Booking
from app.models.user import Role, User
from app.schemas.booking import BookingCreate, BookingRead

# Rezervovať smie každý prihlásený (nielen admin), preto tu nie je require_admin.
# Používateľa potrebujeme v každom endpointe, tak si ho pýtajú priamo funkcie.
router = APIRouter(prefix="/bookings", tags=["bookings"])

# Server v Dockeri beží v UTC, servis je na Slovensku. "Teraz" preto rátame v slovenskom čase,
# inak by sa o 10:30 dal ešte rezervovať termín o 10:00 (v UTC je vtedy len 9:30).
BUSINESS_TZ = ZoneInfo("Europe/Bratislava")

# Ako ďaleko dopredu sa dá rezervovať. To isté číslo má frontend v src/slots.ts.
BOOKING_HORIZON_DAYS = 60

# Najdlhšie obdobie, ktoré vráti jeden GET /bookings. Kalendár si pýta najviac 6 týždňov
# a zoznam najbližších rezervácií 60 dní; väčší rozsah by len zbytočne zaťažil databázu.
MAX_RANGE_DAYS = 62


def _now() -> datetime:
    """Aktuálny čas na Slovensku. Samostatná funkcia, aby ju testy vedeli nahradiť."""
    return datetime.now(BUSINESS_TZ)


def _unprocessable(detail: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)


def _check_slot_is_bookable(booking_date: date, hour: int) -> None:
    """Pravidlá, ktoré schéma nevie overiť, lebo závisia od kalendára a aktuálneho času."""
    now = _now()
    if booking_date.weekday() >= 5:  # weekday(): 0 = pondelok ... 5 = sobota, 6 = nedeľa
        raise _unprocessable("Bookings are possible only from Monday to Friday")
    # Začiatok termínu ako čas v slovenskom pásme, aby sa dal porovnať s "teraz".
    slot_start = datetime.combine(booking_date, time(hour), tzinfo=BUSINESS_TZ)
    if slot_start <= now:
        raise _unprocessable("This slot is already in the past")
    if booking_date > now.date() + timedelta(days=BOOKING_HORIZON_DAYS):
        raise _unprocessable(f"Bookings are possible at most {BOOKING_HORIZON_DAYS} days ahead")


def _to_read(booking: Booking, email: str, viewer: User) -> BookingRead:
    """Pripraví rezerváciu pre konkrétneho diváka: cudzie údaje skryje (pozri BookingRead)."""
    mine = booking.user_id == viewer.id
    visible = mine or viewer.role == Role.ADMIN
    return BookingRead(
        id=booking.id,
        booking_date=booking.booking_date,
        hour=booking.hour,
        mine=mine,
        user_email=email if visible else None,
        note=booking.note if visible else None,
    )


@router.get("", response_model=list[BookingRead])
def list_bookings(
    # Query() bez predvolenej hodnoty = povinný parameter: /bookings?start=2026-11-01&end=2026-11-30
    start: date = Query(),
    end: date = Query(),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obsadené termíny v danom období (vrátane oboch krajných dní)."""
    if end < start:
        raise _unprocessable("end must not be before start")
    if (end - start).days > MAX_RANGE_DAYS:
        raise _unprocessable(f"The range can be at most {MAX_RANGE_DAYS} days")

    # JOIN: ku každej rezervácii rovno načítame email jej majiteľa. Bez neho by sme sa
    # na používateľa pýtali zvlášť pre každý riadok (tzv. N+1 problém).
    rows = db.execute(
        select(Booking, User.email)
        .join(User, Booking.user_id == User.id)
        .where(Booking.booking_date.between(start, end))
        .order_by(Booking.booking_date, Booking.hour)
    ).all()
    return [_to_read(booking, email, user) for booking, email in rows]


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(
    data: BookingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_slot_is_bookable(data.booking_date, data.hour)
    # Majiteľom je vždy prihlásený používateľ z tokenu. Z requestu ho neberieme,
    # inak by sa dalo rezervovať v cudzom mene.
    booking = Booking(user_id=user.id, **data.model_dump())
    db.add(booking)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        diag = getattr(exc.orig, "diag", None)
        if getattr(diag, "constraint_name", None) == SLOT_UNIQUE:
            raise HTTPException(status.HTTP_409_CONFLICT, "This slot is already booked") from exc
        raise
    db.refresh(booking)
    return _to_read(booking, user.email, user)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_booking(
    booking_id: int = Path(ge=1, le=PG_INT_MAX),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    # Zrušiť smie majiteľ svoju rezerváciu, admin hocktorú.
    if booking.user_id != user.id and user.role != Role.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can cancel only your own bookings")
    db.execute(delete(Booking).where(Booking.id == booking_id))
    db.commit()
