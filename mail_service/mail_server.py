# 文件路径: mail_service/mail_server.py (最终简化版)

import smtpd
import asyncore
import sys

class DebuggingServer(smtpd.DebuggingServer):
    # 重写 process_message 方法以美化输出
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        print("\n" + "="*20 + " [DEBUG EMAIL RECEIVED] " + "="*20)
        print(f"From: {mailfrom}")
        print(f"To: {rcpttos}")
        print("-" * 64)
        # 尝试解码邮件内容，如果失败则忽略错误
        try:
            print(data.decode('utf-8', errors='ignore'))
        except Exception as e:
            print(f"[Could not decode email body: {e}]")
        print("="*66 + "\n")
        # 刷新输出缓冲区，确保日志能立即显示
        sys.stdout.flush()

def run_server():
    print(">>> Starting local SMTP debug server on port 8025...")
    # 监听所有网络接口的 8025 端口
    server = DebuggingServer(('0.0.0.0', 8025), None)
    try:
        # 启动事件循环，这将使脚本持续运行
        asyncore.loop()
    except KeyboardInterrupt:
        print("\nShutting down SMTP server.")

# 直接运行服务器
run_server()