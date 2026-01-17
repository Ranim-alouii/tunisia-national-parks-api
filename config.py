from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API Settings
    SECRET_KEY: str = "change-this-secret-key-to-something-random-and-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Admin Credentials
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_FULL_NAME: str = "Park Admin"
    
    # Database
    DATABASE_URL: str = "sqlite:///./tunisia_parks.db"
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
