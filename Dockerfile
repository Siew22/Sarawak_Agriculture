# Dockerfile (强制修复 OpenCV 版)

# --- 阶段 1: 构建阶段 (Builder) ---
FROM python:3.10-slim as builder

# 只安装最基础的工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip

# 【关键步骤 1】先正常安装 requirements.txt
# 注意：这一步虽然会下载错误的 opencv-python，但为了满足 grad-cam 的检查，我们先让它装
RUN pip install --no-cache-dir --prefix="/install" -r requirements.txt

# 【关键步骤 2】这是绝杀！
# 安装完后，强制卸载那个讨厌的完整版 opencv-python
# 然后强制安装 headless 版本
# --prefix="/install" 确保它装在正确的构建目录里
RUN pip uninstall -y opencv-python || true
RUN pip install --no-cache-dir --prefix="/install" opencv-python-headless==4.11.0.86


# --- 阶段 2: 最终运行阶段 (Final) ---
FROM python:3.10-slim

# 同样只保留基础
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 从构建阶段复制已经修正过的库
COPY --from=builder /install /usr/local
COPY ./app ./app
COPY ./models_store ./models_store
COPY ./knowledge_base ./knowledge_base

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]