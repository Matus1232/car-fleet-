from pathlib import Path

from pydantic import Field
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

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def docs_enabled(self) -> bool:
        return self.environment == "development"


settings = Settings()
