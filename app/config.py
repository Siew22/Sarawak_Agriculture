from pydantic_settings import BaseSettings
from typing import Optional, List
# from urllib.parse import quote_plus # <--- 在这里不再需要

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    PROJECT_NAME: str
    SERPAPI_KEY: Optional[str] = None
    ALLOWED_ORIGINS: str

    @property
    def ALLOWED_ORIGINS_LIST(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',')]

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()