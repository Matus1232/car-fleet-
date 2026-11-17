from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env v koreni projektu (config.py -> core -> app -> backend -> koreň). Cesta je odvodená
# od tohto súboru, takže funguje bez ohľadu na to, z ktorého priečinka aplikáciu spustíš.
# V Dockeri súbor neexistuje a premenné prichádzajú z docker-compose.yml.
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    app_name: str = "Car Fleet Manager"
    environment: str = "production"  # "development" zapína /docs a /openapi.json
    database_url: str  # povinné, bez predvolenej hodnoty
    cors_origins: str = ""  # zoznam povolených originov oddelený čiarkou
    # Kľúč, ktorým sa podpisujú JWT tokeny. Kto ho pozná, vie vyrobiť token za hocikoho,
    # preto je povinný a krátky (ľahko uhádnuteľný) kľúč aplikácia odmietne už pri štarte.
    secret_key: str = Field(min_length=32)
    access_token_expire_minutes: int = Field(default=30, ge=1)
    # Ochrana prihlásenia: koľko neúspešných pokusov z jednej IP adresy je povolených
    # za časové okno. Potom /auth/token vracia 429, kým najstarší pokus z okna nevypadne.
    login_max_attempts: int = Field(default=10, ge=1)
    login_window_seconds: int = Field(default=15 * 60, ge=1)
    # Ochrana registrácie: koľko pokusov o vytvorenie účtu je povolených z jednej IP adresy
    # za časové okno. Registrácia je verejná, takže bez limitu by ju skript volal donekonečna.
    register_max_attempts: int = Field(default=10, ge=1)
    register_window_seconds: int = Field(default=60 * 60, ge=1)
    # Cookie s tokenom posiela prehliadač len cez HTTPS. Na Railway beží všetko cez HTTPS, takže
    # True. Testy bežia cez http://testserver, tam ho vypíname (inak by cookie nikto neposlal späť).
    cookie_secure: bool = True
    # Hlavička, v ktorej proxy pred aplikáciou posiela skutočnú IP klienta (na Railway "X-Real-IP").
    # Prázdne = hlavičke neveríme a berieme IP priameho spojenia. Nastav ju len vtedy, keď sa na API
    # nedá dostať inak než cez túto proxy, inak by si ktokoľvek mohol poslať vymyslenú IP.
    client_ip_header: str = ""

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, url: str) -> str:
        """Railway (a Heroku) dávajú adresu ako postgresql://... alebo postgres://...
        SQLAlchemy by pre ňu hľadal ovládač psycopg2, my máme psycopg 3, tak ho povieme výslovne."""
        for prefix in ("postgresql://", "postgres://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url.removeprefix(prefix)
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def docs_enabled(self) -> bool:
        return self.environment == "development"


settings = Settings()
