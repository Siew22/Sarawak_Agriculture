import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 本地调试服务器的固定配置
SMTP_SERVER = "localhost"
SMTP_PORT = 8025
SENDER_EMAIL = "noreply@sarawak-agri.dev" # 虚拟发件人

def send_verification_email(recipient_email: str, code: str) -> bool:
    print(f"\n--- [DEBUG EMAIL] ---")
    print(f"Intending to send an email via local debug server ({SMTP_SERVER}:{SMTP_PORT})")
    print(f"  FROM: {SENDER_EMAIL}")
    print(f"  TO:   {recipient_email}")
    print(f"  CODE: {code}")
    print(f"---------------------\n")

    message = MIMEMultipart("alternative")
    message["Subject"] = "Your Verification Code - Sarawak Agri-Advisor"
    message["From"] = SENDER_EMAIL
    message["To"] = recipient_email
    
    html_content = f"<html><body><p>Your verification code is: <b>{code}</b></p></body></html>"
    message.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
        print(f"✅ Email successfully delivered to local debug server for {recipient_email}")
        return True
    except ConnectionRefusedError:
        print(f"❌ FATAL ERROR: Cannot connect to the local debug email server.")
        print(f"   Please ensure it is running in a separate terminal with the command:")
        print(f"   python -m smtpd -c DebuggingServer -n localhost:8025")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred while sending email: {e}")
        return False