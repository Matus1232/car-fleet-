from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import Token, UserRead, normalize_email

router = APIRouter(prefix="/auth", tags=["auth"])

# Hash, voči ktorému overujeme heslo, keď email v databáze neexistuje. Overenie hesla trvá
# ~50 ms; keby sme pri neznámom emaile odpovedali hneď, útočník by podľa rýchlosti odpovede
# zistil, ktoré emaily sú zaregistrované.
DUMMY_HASH = hash_password("dummy password for timing")


@router.post("/token", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Prihlásenie. OAuth2 štandard volá pole 'username', my doňho píšeme email."""
    user = db.scalar(select(User).where(User.email == normalize_email(form.username)))
    password_ok = verify_password(form.password, user.hashed_password if user else DUMMY_HASH)
    if user is None or not password_ok:
        # Rovnaká chyba pre zlý email aj zlé heslo, aby sa nedalo zistiť, ktorý email existuje.
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
def read_me(user: User = Depends(get_current_user)):
    """Kto som? Frontend to použije po prihlásení, napr. aby vedel, či ukázať admin menu."""
    return user
