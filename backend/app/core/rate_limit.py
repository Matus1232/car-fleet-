import math
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.rate_limit_hit import RateLimitHit


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int) -> None:
        super().__init__(f"Rate limit exceeded, retry after {retry_after} s")
        self.retry_after = retry_after  # o koľko sekúnd sa uvoľní najbližší pokus


def _utc_now() -> datetime:
    return datetime.now(UTC)


class RateLimiter:
    """Povolí najviac `max_attempts` pokusov za posledných `window_seconds` sekúnd pre jeden kľúč.

    Kľúč je napríklad IP adresa. Pre každý kľúč počítame pokusy v "posuvnom okne": staré pokusy
    z okna vypadávajú, takže blokovanie skončí samo, bez ručného odomykania.

    Pokusy sú v PostgreSQL (tabuľka rate_limit_hits), nie v pamäti procesu. Vďaka tomu
    sa nevynulujú po reštarte a pri viacerých procesoch (uvicorn --workers 4) majú všetky
    jedno spoločné počítadlo. Cena: každý pokus = pár malých dopytov do databázy. Pri veľkej
    záťaži by sa počítadlá presunuli do Redisu, ktorý je na to rýchlejší.
    """

    def __init__(
        self,
        scope: str,
        max_attempts: int,
        window_seconds: float,
        clock: Callable[[], datetime] = _utc_now,
        session_factory: Callable[[], Session] = SessionLocal,
    ) -> None:
        self.scope = scope  # oddelí počítadlá prihlásenia a registrácie v jednej tabuľke
        self.max_attempts = max_attempts
        self.window = timedelta(seconds=window_seconds)
        # Testy sem podstrčia vlastné hodiny, aby nemuseli čakať 15 minút.
        self._clock = clock
        # Limiter má vlastné spojenie do databázy, nezávislé od transakcie requestu: pokus sa tak
        # zapíše hneď, aj keď sa zvyšok requestu (napr. registrácia) nepodarí.
        self._session_factory = session_factory

    def acquire(self, key: str) -> int:
        """Zarezervuje pokus a vráti jeho ID. Ak je limit vyčerpaný, vyhodí RateLimitExceeded."""
        now = self._clock()
        window_start = now - self.window
        # "with ... db.begin()" = všetko vnútri je jedna transakcia, na konci sa sama potvrdí.
        with self._session_factory() as db, db.begin():
            # Zámok na tento kľúč do konca transakcie. Bez neho by dva súbežné requesty mohli
            # oba napočítať 9 pokusov, oba prejsť a spolu by ich bolo 11. Requesty s iným kľúčom
            # (iná IP) na seba nečakajú. hashtext() spraví z textu číslo, ktoré zámok potrebuje.
            db.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:lock))"),
                {"lock": f"{self.scope}:{key}"},
            )
            # Upratovanie: pokusy, ktoré už vypadli z okna, netreba držať (pri všetkých kľúčoch,
            # inak by IP, ktorá sa raz pomýlila a viac neprišla, ostala v tabuľke navždy).
            db.execute(
                delete(RateLimitHit).where(
                    RateLimitHit.scope == self.scope, RateLimitHit.created_at <= window_start
                )
            )
            oldest, count = db.execute(
                select(func.min(RateLimitHit.created_at), func.count()).where(
                    RateLimitHit.scope == self.scope, RateLimitHit.key == key
                )
            ).one()
            if count >= self.max_attempts:
                # Najstarší pokus vypadne z okna ako prvý, vtedy sa uvoľní miesto.
                retry_after = (oldest + self.window - now).total_seconds()
                raise RateLimitExceeded(max(1, math.ceil(retry_after)))
            hit = RateLimitHit(scope=self.scope, key=key, created_at=now)
            db.add(hit)
            db.flush()  # pošle INSERT hneď, aby sme poznali hit.id
            return hit.id

    def release(self, key: str, attempt: int) -> None:
        """Vráti zarezervovaný pokus (napríklad pri úspešnom prihlásení sa nepočíta)."""
        with self._session_factory() as db, db.begin():
            db.execute(
                delete(RateLimitHit).where(
                    RateLimitHit.id == attempt,
                    RateLimitHit.scope == self.scope,
                    RateLimitHit.key == key,
                )
            )
