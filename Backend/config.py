import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "CareerHub API"
    DATABASE_URL: str = "sqlite+aiosqlite:///./careerhub.db"

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "fastapi-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    GOOGLE_CLIENT_ID: str = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.environ.get(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:8000/api/auth/google/callback/",
    )

    FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:3000")

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
