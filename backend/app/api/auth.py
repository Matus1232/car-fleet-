from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import RateLimiter, RateLimitExceeded
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import Token, UserRead, normalize_email

router = APIRouter(prefix="/auth", tags=["auth"])

# Hash, voči ktorému overujeme heslo, keď email v databáze neexistuje. Overenie hesla trvá
# ~50 ms; keby sme pri neznámom emaile odpovedali hneď, útočník by podľa rýchlosti odpovede
# zistil, ktoré emaily sú zaregistrované.
DUMMY_HASH = hash_password("dummy password for timing")

# Bez limitu by útočník mohol skúšať heslá donekonečna. Počítame len neúspešné pokusy
# z jednej IP adresy, takže kolegovia za spoločnou firemnou IP sa pri bežnom prihlasovaní
# navzájom nezablokujú. Limit zámerne nie je na email: inak by ktokoľvek mohol pár zlými
# heslami zablokovať prihlásenie admina.
login_limiter = RateLimiter(settings.login_max_attempts, settings.login_window_seconds)


@router.post("/token", response_model=Token)
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Prihlásenie. OAuth2 štandard volá pole 'username', my doňho píšeme email."""
    client_ip = request.client.host if request.client else "unknown"
    try:
        # Pokus si zarezervujeme ešte pred overením hesla, aby ani veľa súbežných
        # requestov naraz neprešlo cez limit. Pri úspechu ho na konci vrátime.
        attempt = login_limiter.acquire(client_ip)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed login attempts, try again later",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc

    user = db.scalar(select(User).where(User.email == normalize_email(form.username)))
    password_ok = verify_password(form.password, user.hashed_password if user else DUMMY_HASH)
    if user is None or not password_ok:
        # Rovnaká chyba pre zlý email aj zlé heslo, aby sa nedalo zistiť, ktorý email existuje.
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    login_limiter.release(client_ip, attempt)  # úspešné prihlásenie sa do limitu nepočíta
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
def read_me(user: User = Depends(get_current_user)):
    """Kto som? Frontend to použije po prihlásení, napr. aby vedel, či ukázať admin menu."""
    return user
