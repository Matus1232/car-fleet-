from pathlib import Path

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

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def docs_enabled(self) -> bool:
        return self.environment == "development"


settings = Settings()
