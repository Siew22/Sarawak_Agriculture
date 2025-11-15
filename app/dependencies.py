from fastapi import Depends, Header, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import Dict, Any

from app import crud, database
from app.auth import security
from app.services import weather_service

# --- 认证依赖 ---
async def get_current_user(token: str = Header(..., alias="Authorization"), db: Session = Depends(database.get_db)) -> database.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token.startswith("Bearer "):
        raise credentials_exception
    
    token_value = token.split(" ")[1]
    email = security.verify_token(token_value, credentials_exception)
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

# --- 天气数据依赖 ---
async def get_weather_data(latitude: float = Form(...), longitude: float = Form(...)) -> Dict[str, Any]:
    try:
        weather_data = await weather_service.get_current_weather(latitude, longitude)
        logger.info(f"Weather data retrieved: Temp={weather_data['temperature']}°C, Humidity={weather_data['humidity']}%")
        return weather_data
    except ConnectionError as e:
        logger.error(f"Weather service connection failed: {e}")
        raise HTTPException(status_code=503, detail="Weather service is currently unavailable.")

# 别忘了导入 loguru
from loguru import logger