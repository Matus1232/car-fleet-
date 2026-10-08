from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Car Fleet Manager"
    database_url: str = "postgresql+psycopg://carfleet:change-me@localhost:5432/carfleet"


settings = Settings()
