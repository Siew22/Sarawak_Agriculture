# app/background_tasks.py
from celery import Celery
import subprocess
from loguru import logger

# 配置Celery
celery_app = Celery('tasks', broker='redis://localhost:6379/0')

@celery_app.task
def trigger_background_retraining():
    """这是一个后台任务，它会启动一个新的进程来运行我们的训练脚本。"""
    logger.info("后台任务启动：开始重新训练AI模型...")
    try:
        # 确保从项目根目录运行
        process = subprocess.Popen(
            ["python", "app/train/train_model_2.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            logger.success("后台再训练成功完成！")
            # 在这里可以加上模型重新加载的逻辑
        else:
            logger.error(f"后台再训练失败: {stderr}")
    except Exception as e:
        logger.error(f"启动后台再训练时发生严重错误: {e}")