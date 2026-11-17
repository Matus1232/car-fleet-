from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import client_ip, get_current_user, get_token
from app.api.users import save_user
from app.core.config import settings
from app.core.rate_limit import RateLimiter, RateLimitExceeded
from app.core.security import (
    ACCESS_COOKIE,
    TokenData,
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.revoked_token import RevokedToken
from app.models.user import Role, User
from app.schemas.user import Token, UserRead, UserRegister, normalize_email

router = APIRouter(prefix="/auth", tags=["auth"])

# Hash, voči ktorému overujeme heslo, keď email v databáze neexistuje. Overenie hesla trvá
# ~50 ms; keby sme pri neznámom emaile odpovedali hneď, útočník by podľa rýchlosti odpovede
# zistil, ktoré emaily sú zaregistrované.
DUMMY_HASH = hash_password("dummy password for timing")

# Bez limitu by útočník mohol skúšať heslá donekonečna. Počítame len neúspešné pokusy
# z jednej IP adresy, takže kolegovia za spoločnou firemnou IP sa pri bežnom prihlasovaní
# navzájom nezablokujú. Limit zámerne nie je na email: inak by ktokoľvek mohol pár zlými
# heslami zablokovať prihlásenie admina.
login_limiter = RateLimiter("login", settings.login_max_attempts, settings.login_window_seconds)

# Registrácia je verejná a každá stojí server ~50 ms hashovania a riadok v databáze. Limit
# na IP adresu bráni skriptu, aby zakladal tisíce účtov alebo skúšal, ktoré emaily už existujú.
register_limiter = RateLimiter(
    "register", settings.register_max_attempts, settings.register_window_seconds
)


def _cookie_options() -> dict:
    """Spoločné nastavenia cookie s tokenom (pri nastavení aj pri mazaní musia byť rovnaké)."""
    return {
        "path": "/",
        # httponly: JavaScript na stránke cookie nevidí (document.cookie ju nevráti),
        # takže token neukradne ani skript podstrčený do stránky (XSS).
        "httponly": True,
        # secure: prehliadač ju pošle len cez HTTPS, nikdy nezašifrovane.
        "secure": settings.cookie_secure,
        # samesite=strict: prehliadač ju nepripojí k requestu, ktorý spustila cudzia stránka.
        # Funguje to, lebo frontend aj API sú na jednej adrese (API je pod /api, pozri nginx.conf).
        "samesite": "strict",
    }


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, request: Request, db: Session = Depends(get_db)):
    """Verejná registrácia: účet si vytvorí ktokoľvek, vždy však len s rolou driver.

    Rolu neberieme z requestu, ale napevno tu. Admin vzniká iba príkazom v termináli
    (app/cli.py) alebo ho založí iný admin cez POST /users.
    """
    try:
        # Na rozdiel od prihlásenia pokus nevraciame: počíta sa každá registrácia, aj úspešná.
        register_limiter.acquire(client_ip(request))
    except RateLimitExceeded as exc:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many registration attempts, try again later",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc

    hashed = hash_password(data.password.get_secret_value())
    # Obsadený email skončí ako 409. Prezradí to, že účet existuje, ale bez overovania emailu
    # sa tomu nedá vyhnúť: človek musí vedieť, prečo sa nezaregistroval.
    return save_user(db, User(email=data.email, hashed_password=hashed, role=Role.DRIVER))


@router.post("/token", response_model=Token)
def login(
    request: Request,
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Prihlásenie. OAuth2 štandard volá pole 'username', my doňho píšeme email.

    Token pošleme dvakrát: v httpOnly cookie (pre frontend) a v tele odpovede (pre Swagger
    a testy). Frontend telo ignoruje. Telo by si mohol prečítať aj podstrčený skript, ale iba
    v okamihu prihlásenia, keď by aj tak videl heslo písané do formulára.
    """
    ip = client_ip(request)
    try:
        # Pokus si zarezervujeme ešte pred overením hesla, aby ani veľa súbežných
        # requestov naraz neprešlo cez limit. Pri úspechu ho na konci vrátime.
        attempt = login_limiter.acquire(ip)
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
    login_limiter.release(ip, attempt)  # úspešné prihlásenie sa do limitu nepočíta

    token = create_access_token(user.id)
    # max_age = cookie zmizne z prehliadača v tom istom čase, keď token vyprší.
    response.set_cookie(
        ACCESS_COOKIE,
        token,
        max_age=settings.access_token_expire_minutes * 60,
        **_cookie_options(),
    )
    return Token(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    token: TokenData = Depends(get_token),
    db: Session = Depends(get_db),
):
    """Odhlásenie: token zaradí medzi zrušené, takže prestane platiť hneď, aj keby ho niekto
    medzitým skopíroval. Potom povie prehliadaču, aby cookie zmazal."""
    # Upratovanie: zrušené tokeny, ktoré by už aj tak neplatili, si netreba pamätať.
    db.execute(delete(RevokedToken).where(RevokedToken.expires_at < datetime.now(UTC)))
    db.add(RevokedToken(jti=token.jti, expires_at=token.expires_at))
    db.commit()
    response.delete_cookie(ACCESS_COOKIE, **_cookie_options())


@router.get("/me", response_model=UserRead)
def read_me(user: User = Depends(get_current_user)):
    """Kto som? Frontend to volá pri štarte: podľa odpovede vie, či je niekto prihlásený
    (cookie sám prečítať nevie, je httpOnly) a či ukázať admin menu."""
    return user
