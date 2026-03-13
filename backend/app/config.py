from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite:///./data/database.db"

    # Crawler
    default_delay_min: int = 1
    default_delay_max: int = 3
    default_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # Frontend
    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


settings = Settings()
