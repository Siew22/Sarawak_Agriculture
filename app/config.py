# app/config.py

from pydantic_settings import BaseSettings
from typing import Optional, List
from urllib.parse import quote_plus

class Settings(BaseSettings):
    """
    Loads ALL application settings from the .env file.
    """
    
    # --- Database Configuration ---
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # --- Application Core Settings ---
    PROJECT_NAME: str
    CONFIDENCE_THRESHOLD: float = 0.75

    # --- External APIs ---
    SERPAPI_KEY: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None
    # --- ↓↓↓ 在这里添加下面这一行 ↓↓↓ ---
    NGROK_AUTHTOKEN: Optional[str] = None 
    
    # --- Email Configuration (for SMTP) ---
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SENDER_EMAIL: str
    SENDER_PASSWORD: Optional[str] = None
    
    # --- CORS Configuration ---
    ALLOWED_ORIGINS: str

    @property
    def ALLOWED_ORIGINS_LIST(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',')]

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()