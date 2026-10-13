from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

# Algoritmus podpisu tokenu. HS256 = HMAC-SHA256 s jedným tajným kľúčom (settings.secret_key).
ALGORITHM = "HS256"

# Odporúčané nastavenie knižnice pwdlib, dnes je to Argon2 (zámerne pomalý hash).
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    # Do tokenu dávame len ID, nie rolu: rolu načítame pri každom requeste z databázy,
    # takže zmena roly (alebo zmazanie používateľa) platí hneď, nie až keď token vyprší.
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Vráti ID používateľa z platného tokenu, inak None (zlý podpis, vypršaný, poškodený)."""
    try:
        # algorithms musí byť zadaný natvrdo. Keby sme verili algoritmu z hlavičky tokenu,
        # útočník by si tam mohol napísať "none" (bez podpisu) a server by mu uveril.
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[ALGORITHM], options={"require": ["exp", "sub"]}
        )
        return int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError):
        return None
