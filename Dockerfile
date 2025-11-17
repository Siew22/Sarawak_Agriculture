# Dockerfile (最终生产版 v3)

# --- 阶段 1: 构建阶段 (Builder) ---
FROM python:3.10-slim as builder

# 【【【 核心修复 1 】】】
# 安装一个更完整的系统依赖包集合，确保 OpenCV 的所有底层需求都被满足
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir --prefix="/install" -r requirements.txt


# --- 阶段 2: 最终运行阶段 (Final) ---
FROM python:3.10-slim

# 【【【 核心修复 2 】】】
# 在最终镜像中也安装同样的、完整的系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 从构建阶段复制已安装的依赖
COPY --from=builder /install /usr/local

# 只复制应用运行所必需的文件夹
COPY ./app ./app
COPY ./models_store ./models_store
COPY ./knowledge_base ./knowledge_base

EXPOSE 8000

# 启动命令保持不变
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]