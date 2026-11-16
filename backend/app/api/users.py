from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import EMAIL_UNIQUE, User
from app.schemas.user import UserCreate, UserRead

# Tento router je len pre admina: vie založiť účet s ľubovoľnou rolou, teda aj ďalšieho admina.
# Ostatní sa registrujú sami cez POST /auth/register, kde vždy vznikne rola "driver".
router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_admin)])


def build_user(data: UserCreate) -> User:
    hashed = hash_password(data.password.get_secret_value())
    return User(email=data.email, hashed_password=hashed, role=data.role)


def save_user(db: Session, user: User) -> User:
    """Uloží nového používateľa. Obsadený email premení na 409 (používa to aj registrácia)."""
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        diag = getattr(exc.orig, "diag", None)
        if getattr(diag, "constraint_name", None) == EMAIL_UNIQUE:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "A user with this email already exists"
            ) from exc
        raise
    db.refresh(user)
    return user


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    return save_user(db, build_user(data))
