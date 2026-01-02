from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Admin Credentials (dev only; later move to DB)
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    ADMIN_FULL_NAME: str = "Park Admin"

    # Database
    DATABASE_URL: str = "sqlite:///./tunisia_parks.db"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000"

    # Weather API
    OPENWEATHER_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
