from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "CareerHub API"
    DATABASE_URL: str = "sqlite+aiosqlite:///./careerhub.db"

    SECRET_KEY: str = "fastapi-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback/"

    FRONTEND_URL: str = "http://localhost:3000"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    RATE_LIMIT: int = 120
    RATE_LIMIT_WINDOW: int = 60

    model_config = {
        "env_file": ".env",
        "extra": "allow",
    }


settings = Settings()
