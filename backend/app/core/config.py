from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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
