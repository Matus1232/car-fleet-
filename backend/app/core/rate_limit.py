import math
import time
from collections import defaultdict, deque
from collections.abc import Callable
from threading import Lock


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int) -> None:
        super().__init__(f"Rate limit exceeded, retry after {retry_after} s")
        self.retry_after = retry_after  # o koľko sekúnd sa uvoľní najbližší pokus


class RateLimiter:
    """Povolí najviac `max_attempts` pokusov za posledných `window_seconds` sekúnd pre jeden kľúč.

    Kľúč je napríklad IP adresa. Pre každý kľúč si pamätáme časy pokusov ("posuvné okno"):
    staré pokusy z okna vypadávajú, takže blokovanie skončí samo, bez ručného odomykania.

    Dáta sú len v pamäti procesu: po reštarte sa vynulujú a pri viacerých procesoch
    (uvicorn --workers 4) by mal každý vlastné počítadlo. Pre jeden proces to stačí,
    pri škálovaní by sa počítadlá presunuli napríklad do Redisu.
    """

    def __init__(
        self,
        max_attempts: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        # time.monotonic, nie time.time: nemení sa, keď niekto posunie systémové hodiny.
        # Testy sem podstrčia vlastné hodiny, aby nemuseli čakať 15 minút.
        self._clock = clock
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._last_sweep = clock()
        # Synchrónne endpointy FastAPI bežia vo viacerých vláknach naraz. Bez zámku by dva
        # súbežné requesty mohli oba prejsť kontrolou skôr, než si ktorýkoľvek zapíše pokus.
        self._lock = Lock()

    def acquire(self, key: str) -> float:
        """Zarezervuje pokus a vráti jeho čas. Ak je limit vyčerpaný, vyhodí RateLimitExceeded."""
        with self._lock:
            now = self._clock()
            self._sweep(now)
            attempts = self._attempts[key]
            self._drop_expired(attempts, now)
            if len(attempts) >= self.max_attempts:
                # Najstarší pokus vypadne z okna ako prvý, vtedy sa uvoľní miesto.
                retry_after = attempts[0] + self.window_seconds - now
                raise RateLimitExceeded(max(1, math.ceil(retry_after)))
            attempts.append(now)
            return now

    def release(self, key: str, attempt: float) -> None:
        """Vráti zarezervovaný pokus (napríklad pri úspešnom prihlásení sa nepočíta)."""
        with self._lock:
            attempts = self._attempts.get(key)
            if attempts and attempt in attempts:
                attempts.remove(attempt)
                if not attempts:
                    del self._attempts[key]

    def reset(self) -> None:
        with self._lock:
            self._attempts.clear()

    def tracked_keys(self) -> int:
        with self._lock:
            return len(self._attempts)

    def _drop_expired(self, attempts: deque[float], now: float) -> None:
        # Časy pribúdajú na koniec, takže najstarší je vždy vpredu.
        while attempts and attempts[0] <= now - self.window_seconds:
            attempts.popleft()

    def _sweep(self, now: float) -> None:
        """Raz za okno zmaže kľúče bez platných pokusov, aby pamäť nerástla donekonečna
        (IP adresa, ktorá sa raz pomýlila a už neprišla, by tu inak ostala navždy)."""
        if now - self._last_sweep < self.window_seconds:
            return
        self._last_sweep = now
        for key in list(self._attempts):
            self._drop_expired(self._attempts[key], now)
            if not self._attempts[key]:
                del self._attempts[key]
