from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import Role, User

# Vytiahne token z hlavičky "Authorization: Bearer <token>". Ak hlavička chýba, sám vráti 401.
# tokenUrl hovorí Swaggeru (/docs), kam má tlačidlo Authorize posielať meno a heslo.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Autentifikácia: zistí, KTO posiela request. Pri akomkoľvek probléme vráti 401."""
    credentials_error = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},  # štandard HTTP: povie klientovi, ako sa prihlásiť
    )
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_error
    user = db.get(User, user_id)
    if user is None:  # token je platný, ale používateľa medzitým zmazali
        raise credentials_error
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Autorizácia: vieme, kto si (vďaka get_current_user), teraz overíme, či to smieš."""
    if user.role != Role.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role required")
    return user
