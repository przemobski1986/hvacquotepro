from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List

class Settings(BaseSettings):
    ENV: str = "dev"
    APP_NAME: str = "HVACQuotePro"
    API_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    DATABASE_URL: str = "postgresql+psycopg://hvac:hvacpass@localhost:5432/hvacquotepro"

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Optional storage (future)
    S3_ENDPOINT_URL: str | None = None
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None
    S3_BUCKET: str | None = None

    def cors_list(self) -> List[str]:
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
