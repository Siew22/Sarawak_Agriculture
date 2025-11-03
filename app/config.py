# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sarawak Agri-Advisor"
    CONFIDENCE_THRESHOLD: float = 0.75
    
    # 未来可以把数据库URL, API密钥等都放在这里
    DATABASE_URL: str = "sqlite:///./database.db"
    OPEN_METEO_API_URL: str = "https://api.open-meteo.com/v1/forecast"

    class Config:
        case_sensitive = True

# 创建一个全局配置实例
settings = Settings()