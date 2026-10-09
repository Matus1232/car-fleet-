from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Car Fleet Manager"
    database_url: str = "postgresql+psycopg2://carfleet:change-me@localhost:5432/carfleet"

    class Config:
        env_file = ".env"

settings = Settings()