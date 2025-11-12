from pydantic_settings import BaseSettings
from typing import Optional, List
from urllib.parse import quote_plus
from dotenv import load_dotenv # <--- 导入
import os
# from urllib.parse import quote_plus # <--- 在这里不再需要

# --- 强制加载 .env 文件 ---
# 这会确保在任何配置被读取之前，.env 文件的内容都已加载到环境变量中
load_dotenv()

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    PROJECT_NAME: str
    SERPAPI_KEY: Optional[str] = None
    ALLOWED_ORIGINS: str
    SMTP_SERVER: str
    SMTP_PORT: int
    SENDER_EMAIL: str
    SENDER_PASSWORD: str
    RESEND_API_KEY: str

    @property
    def ALLOWED_ORIGINS_LIST(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',')]

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()