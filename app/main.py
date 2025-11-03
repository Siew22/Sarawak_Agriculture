# app/main.py (为你重构和优化的最终专业版)

# -----------------------------------------------------------------------------
# 1. 启动与配置 (Startup & Configuration)
# -----------------------------------------------------------------------------
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

# --- 关键优化：在所有其他导入之前，安全地配置matplotlib ---
temp_mpl_dir = Path(__file__).resolve().parent.parent / "temp" / "mpl_config"
os.makedirs(temp_mpl_dir, exist_ok=True)
os.environ['MPLCONFIGDIR'] = str(temp_mpl_dir)
# --- 修改结束 ---

import torch
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger # 统一使用 Loguru

# --- 关键优化：分组导入，更清晰 ---
# 导入应用配置
from .config import settings
# 导入数据模型 (Schemas)
from .schemas.diagnosis import FullDiagnosisReport, PredictionResult
from .schemas.prediction import RiskPredictionResponse
# 导入核心服务和工具
from .utils.image_processing import image_processor
from .utils.xai_generator import xai_generator, save_xai_image
from .models.disease_classifier import classifier
from .models.risk_assessor import risk_assessor
from .models.recommendation_generator import report_generator_v3 as report_generator
from .services.weather_service import weather_service
from .services.disease_predictor_service import disease_predictor_service
from .services.knowledge_discovery_service import knowledge_discovery_service
from .background_tasks import trigger_background_retraining
from .services.data_management_service import data_management_service # 假设我们有一个新服务来管理数据
from .services.knowledge_base_service import kb_service
# --- 导入结束 ---

# --- 应用初始化 ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="一个基于AI和软计算的智能农业诊断系统。V3.0实现了XAI模型可解释性与未来病害风险预测。",
    version="3.0.0",
    # 可以在这里添加更多OpenAPI元数据
    contact={"name": "Siew Seng", "email": "your_email@example.com"},
)

# 挂载静态文件目录
static_path = Path(__file__).resolve().parent.parent / "static"
os.makedirs(static_path / "xai_images", exist_ok=True) # 确保XAI图片文件夹存在
app.mount("/static", StaticFiles(directory=static_path), name="static")

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# 2. API生命周期事件 (Lifecycle Events)
# -----------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    logger.info(f"启动 {settings.PROJECT_NAME} API v3.0...")
    logger.info(f"AI模型已在设备 {classifier.device} 上准备就绪。")
    if xai_generator: logger.info("XAI (Grad-CAM) 模块已成功初始化。")
    else: logger.warning("XAI (Grad-CAM) 模块初始化失败。")
    logger.info("所有服务和模块已初始化。应用启动完成。")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"关闭 {settings.PROJECT_NAME} API...")

# -----------------------------------------------------------------------------
# 3. 依赖注入 (Dependency Injection)
# -----------------------------------------------------------------------------
async def get_weather_data(
    latitude: float = Form(..., description="用户设备的GPS纬度", ge=-90, le=90),
    longitude: float = Form(..., description="用户设备的GPS经度", ge=-180, le=180)
) -> Dict[str, Any]:
    try:
        weather_data = await weather_service.get_current_weather(latitude, longitude)
        logger.info(f"获取当前天气成功: Temp={weather_data['temperature']}°C, Humidity={weather_data['humidity']}%")
        return weather_data
    except ConnectionError as e:
        logger.error(f"天气服务连接失败: {e}")
        raise HTTPException(status_code=503, detail="天气服务当前不可用，请稍后再试。")

# -----------------------------------------------------------------------------
# 4. API 端点 (API Endpoints)
# -----------------------------------------------------------------------------
@app.get("/", summary="API 健康检查", tags=["General"])
def read_root():
    return {"status": "ok", "message": f"欢迎使用 {settings.PROJECT_NAME} API V3！"}

@app.post("/diagnose", response_model=FullDiagnosisReport, summary="获取或探索作物健康诊断报告", tags=["Diagnosis"])
async def create_diagnosis_report(
    image: UploadFile = File(..., description="待诊断的作物叶片图片"),
    weather: Dict[str, Any] = Depends(get_weather_data),
    language: str = Form("en", description="期望的报告语言 (en, ms, zh)", enum=["en", "ms", "zh"])
):
    try:
        image_bytes = await image.read()
        image_tensor = image_processor.process(image_bytes)
        
        prediction = classifier.predict(image_tensor)
        logger.info(f"模型最高预测: {prediction}")

        risk = risk_assessor.assess(weather["temperature"], weather["humidity"])
        logger.info(f"环境风险评估: Level={risk.risk_level}, Score={risk.risk_score:.2f}")

        # --- ↓↓↓ 终极的“自学习”逻辑框架！↓↓↓ ---
        
        if prediction.confidence < settings.CONFIDENCE_THRESHOLD or prediction.disease == "未知病害":
            # 情况一：AI不认识，触发“探索与学习”模式
            logger.warning(f"置信度 ({prediction.confidence:.2%}) 过低，触发“探索与学习”模式...")
            
            # 1. 知识发现
            new_knowledge, new_images = await knowledge_discovery_service.discover(image_bytes, language)
            
            if new_knowledge:
                # 2. 自动扩充数据和知识库
                logger.info("发现新知识！正在自动扩充数据集...")
                new_class_name = data_management_service.add_new_images(new_images) # 将新图片存入新类别文件夹
                kb_service.add_new_entry(new_class_name, new_knowledge)
                # nlg_service.add_new_training_data(...) # 扩充NLG教材
                
                # 3. 触发后台自动再训练 (这是一个异步任务，会立即返回)
                logger.info("数据已扩充，正在触发后台自动再训练...")
                trigger_background_retraining.delay()
                
                # 4. 将本次发现的新知识，实时地、动态地生成报告返回给用户
                logger.info("正在为用户生成本次发现的临时报告...")
                report = report_generator.generate_from_new_knowledge(new_knowledge, risk, language)
                
            else:
                # 如果网络搜索也失败了，才返回最终的“未知”报告
                logger.warning("网络探索失败，返回标准的不确定报告。")
                report = report_generator.generate(prediction, risk, lang=language)
        
        else:
            # 情况二：AI认识，走正常流程
            logger.info("高置信度诊断，生成标准报告。")
            report = report_generator.generate(prediction, risk, lang=language)
        
        # --- ↑↑↑ 自学习逻辑结束 ↑↑↑ ---
        
        # 5. 生成XAI并附加到报告
        if xai_generator and report:
            xai_url = await _generate_and_attach_xai(image_tensor, image_bytes, prediction.disease)
            if xai_url:
                report.xai_image_url = xai_url
        
        return report

    except Exception as e:
        logger.error(f"处理诊断请求时发生未知服务器错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部发生意外错误。")

@app.post("/predict_risk", response_model=RiskPredictionResponse, summary="预测未来7天病害爆发风险", tags=["Prediction"])
async def predict_disease_risk(
    latitude: float = Form(..., description="用户设备的GPS纬度"),
    longitude: float = Form(..., description="用户设备的GPS经度"),
    disease_key: str = Form(..., description="要预测的病害内部密钥 (例如 'Footrot')")
):
    try:
        forecast_data = await weather_service.get_7_day_forecast(latitude, longitude)
        # --- 关键优化：更健壮的空值检查 ---
        if not forecast_data or not forecast_data.get("time"):
            raise HTTPException(status_code=503, detail="无法获取有效的天气预报数据，请稍后再试。")

        daily_risks = disease_predictor_service.predict_daily_risk(forecast_data, disease_key)
        disease_name = disease_predictor_service.get_disease_display_name(disease_key)
        
        return RiskPredictionResponse(
            disease_name=disease_name,
            location={"latitude": latitude, "longitude": longitude},
            daily_risks=daily_risks
        )
    except (ValueError, KeyError) as e:
        # 捕获已知的数据或逻辑错误，返回 400 Bad Request
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"预测风险时发生未知错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误，无法完成风险预测。")

# -----------------------------------------------------------------------------
# 5. 辅助函数 (Helper Functions)
# -----------------------------------------------------------------------------
async def _generate_and_attach_xai(image_tensor: torch.Tensor, image_bytes: bytes, predicted_class: str) -> Optional[str]:
    """辅助函数，将XAI生成逻辑从主API端点中分离出来，增加了更精确的类型注解。"""
    try:
        target_idx = classifier.get_class_index(predicted_class)
        if target_idx is None:
            logger.warning(f"在XAI生成中找不到类别 '{predicted_class}' 的索引。")
            return None

        logger.info("正在生成XAI (Grad-CAM) 热力图...")
        heatmap_image = xai_generator.generate_heatmap(
            image_tensor=image_tensor.to(classifier.device),
            image_bytes=image_bytes,
            target_category=target_idx
        )
        
        unique_filename = f"xai_{uuid.uuid4().hex}"
        save_xai_image(heatmap_image, unique_filename)
        
        return f"/static/xai_images/{unique_filename}.jpg"
    except Exception as e:
        logger.error(f"生成XAI热力图时失败: {e}", exc_info=True)
        return None