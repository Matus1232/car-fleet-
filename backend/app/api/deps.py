from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import ACCESS_COOKIE, TokenData, decode_access_token
from app.db.session import get_db
from app.models.revoked_token import RevokedToken
from app.models.user import Role, User

# Token môže prísť dvoma cestami:
# 1. httpOnly cookie: tak ho posiela náš frontend. JavaScript na stránke cookie neprečíta,
#    takže token neukradne ani skript, ktorý by sa do stránky dostal (XSS).
# 2. Hlavička "Authorization: Bearer <token>": tak ho posiela Swagger (/docs) a testy.
# auto_error=False: keď hlavička chýba, nevyhodí hneď 401, ešte skúsime cookie.
# tokenUrl hovorí Swaggeru (/docs), kam má tlačidlo Authorize posielať meno a heslo.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

# Ochrana proti CSRF. Prehliadač pridá cookie ku KAŽDÉMU requestu na našu adresu, aj keď ho
# spustí cudzia stránka (napr. skrytý formulár, ktorý odošle POST /bookings). Formulár ani
# obrázok však nevie pridať vlastnú hlavičku a cudzí fetch s ňou CORS zablokuje. Preto pri
# zmenách cez cookie vyžadujeme túto hlavičku: náš frontend ju posiela vždy, cudzia stránka nevie.
# Druhou poistkou je SameSite=Strict na cookie (pozri auth.py).
CSRF_HEADER = "X-Requested-With"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}  # len čítajú, nič nemenia


def _credentials_error() -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},  # štandard HTTP: povie klientovi, ako sa prihlásiť
    )


def get_token(
    request: Request,
    bearer: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> TokenData:
    """Nájde a overí token z hlavičky alebo z cookie. Pri akomkoľvek probléme vráti 401."""
    raw = bearer or request.cookies.get(ACCESS_COOKIE)
    if raw is None:
        raise _credentials_error()
    if bearer is None and request.method not in SAFE_METHODS and CSRF_HEADER not in request.headers:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Missing {CSRF_HEADER} header")

    token = decode_access_token(raw)
    if token is None:
        raise _credentials_error()
    # Odhlásený token: podpis aj čas platnosti sedia, ale používateľ ho už zrušil.
    if db.get(RevokedToken, token.jti) is not None:
        raise _credentials_error()
    return token


def get_current_user(token: TokenData = Depends(get_token), db: Session = Depends(get_db)) -> User:
    """Autentifikácia: zistí, KTO posiela request. Pri akomkoľvek probléme vráti 401."""
    user = db.get(User, token.user_id)
    if user is None:  # token je platný, ale používateľa medzitým zmazali
        raise _credentials_error()
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Autorizácia: vieme, kto si (vďaka get_current_user), teraz overíme, či to smieš."""
    if user.role != Role.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role required")
    return user


def client_ip(request: Request) -> str:
    """IP adresa klienta, podľa ktorej počítame pokusy v rate limiteri.

    Za proxy (Railway, nginx) je IP priameho spojenia vždy IP tej proxy, takže všetci ľudia
    by zdieľali jedno počítadlo. Skutočnú IP posiela proxy v hlavičke (settings.client_ip_header).
    Tej veríme len keď je nastavená: priamo z internetu by si ju klient vedel vymyslieť.
    """
    if settings.client_ip_header:
        forwarded = request.headers.get(settings.client_ip_header, "").strip()
        if forwarded:
            return forwarded[:64]  # stĺpec key má 64 znakov; IPv6 adresa má najviac 45
    return request.client.host if request.client else "unknown"
