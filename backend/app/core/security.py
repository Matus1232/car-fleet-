import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

# Algoritmus podpisu tokenu. HS256 = HMAC-SHA256 s jedným tajným kľúčom (settings.secret_key).
ALGORITHM = "HS256"

# Názov cookie, v ktorej prehliadač nosí token.
ACCESS_COOKIE = "access_token"

# Odporúčané nastavenie knižnice pwdlib, dnes je to Argon2 (zámerne pomalý hash).
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


@dataclass(frozen=True)
class TokenData:
    """Čo vieme z platného tokenu: komu patrí, jeho jedinečné ID a kedy vyprší."""

    user_id: int
    jti: str  # "JWT ID": podľa neho vieme jeden konkrétny token zneplatniť pri odhlásení
    expires_at: datetime


def create_access_token(user_id: int) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    # Do tokenu dávame len ID, nie rolu: rolu načítame pri každom requeste z databázy,
    # takže zmena roly (alebo zmazanie používateľa) platí hneď, nie až keď token vyprší.
    # jti je náhodný reťazec, každý token má iný. secrets (nie random) = vhodné pre bezpečnosť.
    payload = {"sub": str(user_id), "exp": expire, "jti": secrets.token_urlsafe(16)}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> TokenData | None:
    """Údaje z platného tokenu, inak None (zlý podpis, vypršaný, poškodený, chýba údaj)."""
    try:
        # algorithms musí byť zadaný natvrdo. Keby sme verili algoritmu z hlavičky tokenu,
        # útočník by si tam mohol napísať "none" (bez podpisu) a server by mu uveril.
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub", "jti"]},
        )
        return TokenData(
            user_id=int(payload["sub"]),
            jti=str(payload["jti"]),
            expires_at=datetime.fromtimestamp(payload["exp"], UTC),
        )
    except (jwt.InvalidTokenError, ValueError):
        return None
