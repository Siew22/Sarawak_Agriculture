# app/dependencies.py (完整修复版)

from fastapi import Depends, Header, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import Dict, Any
from loguru import logger # <-- 核心添加: 确保导入了 loguru

from app import crud, database
from app.auth import security
from app.services.weather_service import weather_service

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
        # 调用 weather_service 实例上的 get_current_weather 方法
        weather_data = await weather_service.get_current_weather(latitude, longitude)
        
        # 【【【 核心添加: 增强日志记录 】】】
        # 这样我们在后端日志里就能清楚地看到获取到的天气数据
        logger.info(f"Weather data retrieved: Temp={weather_data['temperature']}°C, Humidity={weather_data['humidity']}%")
        
        return weather_data
    except ConnectionError as e:
        # 【【【 核心添加: 增强日志记录 】】】
        logger.error(f"Weather service connection failed: {e}")
        raise HTTPException(status_code=503, detail="Weather service is currently unavailable.")

# 注意: 在您的原始文件中，您在 get_weather_data 内部单独导入了 logger。
# 更好的做法是在文件顶部统一导入。我已按照这种更规范的方式进行了修改。
# 如果您想保持原始风格，可以将文件顶部的 `from loguru import logger` 移动到函数内部。