# 文件路径: mail_service/Dockerfile (最终简化版)

FROM python:3.10-slim

WORKDIR /app

COPY mail_server.py .

# 直接运行 Python 脚本作为启动命令
CMD ["python", "-u", "mail_server.py"]