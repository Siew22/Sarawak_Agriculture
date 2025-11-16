# app/services/email_service.py (简化版)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMultipart
from app.config import settings

def send_verification_email(recipient_email: str, code: str) -> bool:
    # 如果没有配置SMTP服务器，直接打印到控制台并返回成功
    if not settings.SMTP_SERVER or not settings.SMTP_PORT:
        print("\n--- [DEBUG EMAIL (NO SMTP SERVER)] ---")
        print(f"  TO:   {recipient_email}")
        print(f"  CODE: {code}")
        print("--------------------------------------\n")
        return True

    message = MIMultipart("alternative")
    message["Subject"] = "Your Verification Code - Sarawak Agri-Advisor"
    message["From"] = settings.SENDER_EMAIL
    message["To"] = recipient_email
    
    html_content = f"<html><body><p>Your verification code is: <b>{code}</b></p></body></html>"
    message.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.sendmail(settings.SENDER_EMAIL, recipient_email, message.as_string())
        print(f"✅ Verification email for {recipient_email} sent to debug server.")
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed to send email to debug server: {e}")
        return False