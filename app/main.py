# ====================================================================
#  app/main.py (Final & Optimized Version)
# ====================================================================

# --- Part 1: Pre-emptive Configuration ---
import os
from pathlib import Path

# 安全地配置matplotlib
temp_mpl_dir = Path(__file__).resolve().parent.parent / "temp" / "mpl_config"
os.makedirs(temp_mpl_dir, exist_ok=True)
os.environ['MPLCONFIGDIR'] = str(temp_mpl_dir)


# --- Part 2: Standard & App Imports ---
import uuid
import shutil
from typing import Dict, Any, Optional

from fastapi import (
    FastAPI, File, UploadFile, HTTPException,
    Form, Depends, Header, status, Request
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
import torch
from sqlalchemy.orm import Session

# --- 数据库初始化 (保持在应用逻辑前) ---
from app import database
database.Base.metadata.create_all(bind=database.engine)

# --- 应用模块导入 ---
from app.config import settings
from app.schemas import diagnosis as schemas_diagnosis
from app.schemas import prediction as schemas_prediction
from app.utils import image_processing, xai_generator
from app.models import disease_classifier, risk_assessor, recommendation_generator
from app.services.weather_service import weather_service
from app.services.disease_predictor_service import disease_predictor_service
from app.services.knowledge_discovery_service import knowledge_discovery_service
from app.services.data_management_service import data_management_service
from app.services.knowledge_base_service import kb_service
from app.services import permission_service
from app.background_tasks import trigger_background_retraining
# 确保导入了所有路由模块
from app.routers import users, token, diagnoses, products, posts, orders, chat
from app import crud
# 依赖项
from app.dependencies import get_current_user, get_weather_data
from fastapi.responses import JSONResponse 


# --- Part 3: FastAPI Application Setup ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="An AI-powered agricultural diagnosis system with subscriptions and permissions.",
    version="3.2.0",
)

# --- 【【【 核心修复：添加全局异常处理器 】】】 ---
# 这个处理器会捕获所有未被处理的服务器内部错误
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # 打印详细的错误日志到后端控制台，方便我们调试
    print(f"--- UNHANDLED EXCEPTION ---")
    import traceback
    traceback.print_exc()
    print(f"---------------------------")
    
    # 无论发生什么错误，都向前端返回一个标准的 JSON 错误响应
    return JSONResponse(
        status_code=500,
        content={"detail": f"An internal server error occurred: {exc}"},
    )

# --- 中间件 (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sarawak-agriculture.vercel.app",
        "https://*.vercel.app",
        "https://*.ngrok-free.app",
        "https://*.ngrok.io",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 静态文件 ---
static_path = Path(__file__).resolve().parent.parent / "static"
(static_path / "uploads").mkdir(parents=True, exist_ok=True)
(static_path / "xai_images").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# --- 路由注册 (干净、无重复) ---
app.include_router(token.router) # 登录/认证路由
app.include_router(users.router) # 用户相关路由
app.include_router(diagnoses.router) # 诊断历史路由
app.include_router(products.router) # 商品路由
app.include_router(posts.router) # 社区帖子路由
app.include_router(orders.router) # 订单路由
app.include_router(chat.router) # 聊天路由


# --- Part 4: API 生命周期 ---
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting up {settings.PROJECT_NAME} API...")
    logger.info(f"AI model ready on device: {disease_classifier.classifier.device}")
    if xai_generator.xai_generator:
        logger.info("XAI (Grad-CAM) module initialized.")
    else:
        logger.warning("XAI (Grad-CAM) module failed to initialize.")
    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.PROJECT_NAME} API...")


# --- Part 5: API 端点 (只保留根路径和核心功能) ---
@app.get("/", summary="API Health Check", tags=["General"])
def read_root():
    return {"status": "ok", "message": f"Welcome to {settings.PROJECT_NAME} API!"}

@app.post("/diagnose", response_model=schemas_diagnosis.FullDiagnosisReport, summary="Get crop health diagnosis", tags=["Diagnosis"])
async def create_diagnosis_report(
    image: UploadFile = File(...),
    language: str = Form("en", enum=["en", "ms", "zh"]),
    weather: Dict[str, Any] = Depends(get_weather_data),
    current_user: database.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    logger.info(f"User '{current_user.email}' (ID: {current_user.id}) performing diagnosis.")
    
    permission_service.check_api_limit(db, user=current_user)

    try:
        unique_filename = f"{uuid.uuid4().hex}{Path(image.filename).suffix.lower()}"
        file_path = static_path / "uploads" / unique_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        image_url = f"/static/uploads/{unique_filename}"
        image.file.seek(0)
        image_bytes = await image.read()
        
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Error saving image file.")

    try:
        image_tensor = image_processing.image_processor.process(image_bytes)
        prediction = disease_classifier.classifier.predict(image_tensor)
        risk = risk_assessor.risk_assessor.assess(weather["temperature"], weather["humidity"])
        
        report = recommendation_generator.report_generator_v3.generate(prediction, risk, lang=language)

        if xai_generator.xai_generator and report:
            xai_url = await _generate_and_attach_xai(image_tensor, image_bytes, prediction.disease)
            if xai_url:
                report.xai_image_url = xai_url

        permission_service.log_api_usage(db, user_id=current_user.id, endpoint="/diagnose")
        crud.create_diagnosis_history(
            db=db, user_id=current_user.id, report=report,
            prediction=prediction, risk=risk, image_url=image_url
        )
        logger.success(f"Diagnosis and history saved for user ID: {current_user.id}")
        
        return report

    except Exception as e:
        logger.error(f"An unexpected error occurred during diagnosis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred during diagnosis.")

@app.post("/predict_risk", response_model=schemas_prediction.RiskPredictionResponse, summary="Predict future 7-day disease risk", tags=["Prediction"])
async def predict_disease_risk(
    latitude: float = Form(...),
    longitude: float = Form(...),
    disease_key: str = Form(...)
):
    try:
        forecast_data = await weather_service.get_7_day_forecast(latitude, longitude)
        if not forecast_data:
            raise HTTPException(status_code=503, detail="Unable to retrieve valid weather forecast data.")

        daily_risks = disease_predictor_service.predict_daily_risk(forecast_data, disease_key)
        
        kb_info = kb_service.get_disease_info(disease_key)
        disease_name = kb_info.get("name", {}).get("en", disease_key) if kb_info else disease_key
        
        return schemas_prediction.RiskPredictionResponse(
            disease_name=disease_name,
            location={"latitude": latitude, "longitude": longitude},
            daily_risks=daily_risks
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during risk prediction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during risk prediction.")
        
async def _generate_and_attach_xai(image_tensor: torch.Tensor, image_bytes: bytes, predicted_class: str) -> Optional[str]:
    """
    Helper function to generate and save XAI heatmap.
    """
    try:
        target_idx = disease_classifier.classifier.get_class_index(predicted_class)
        if target_idx is None:
            logger.warning(f"Cannot find class index for '{predicted_class}' in XAI.")
            return None
        
        heatmap = xai_generator.xai_generator.generate_heatmap(
            image_tensor=image_tensor.to(disease_classifier.classifier.device), 
            image_bytes=image_bytes, 
            target_category=target_idx
        )
        
        unique_filename = f"xai_{uuid.uuid4().hex}"
        xai_generator.save_xai_image(heatmap, unique_filename)
        
        return f"/static/xai_images/{unique_filename}.jpg"
    except Exception as e:
        logger.error(f"Failed to generate XAI heatmap: {e}", exc_info=True)
        return None
    
