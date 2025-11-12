import resend
from app.config import settings

# 在模块加载时就设置好API Key
# 确保 resend.api_key 不是 None
if settings.RESEND_API_KEY:
    resend.api_key = settings.RESEND_API_KEY
else:
    print("CRITICAL: RESEND_API_KEY is not set. Resend is disabled.")

def send_verification_email(recipient_email: str, code: str) -> bool:
    # 在函数开始时再次检查，以防万一
    if not resend.api_key:
        return False

    # --- 这是最关键的部分 ---
    # 确保发件人邮箱严格来自我们的配置文件
    sender_email = settings.SENDER_EMAIL
    
    # 调试打印，确认我们使用了正确的发件人和收件人
    print(f"--- Preparing to send email ---")
    print(f"FROM: {sender_email}")
    print(f"TO: {recipient_email}")
    print(f"-----------------------------")

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f7fafc; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
          <h2 style="color: #2d3748; margin-bottom: 20px;">🔐 Verification Code</h2>
          <p style="color: #4a5568; font-size: 16px;">Your verification code for <strong>account activation</strong> is:</p>
          <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; text-align: center; margin: 25px 0; border-radius: 8px;">
            <h1 style="color: white; letter-spacing: 8px; margin: 0; font-size: 36px;">{code}</h1>
          </div>
          <p style="color: #718096; font-size: 14px;">⏱️ This code will expire in <strong>10 minutes</strong>.</p>
        </div>
      </body>
    </html>
    """

    try:
        params = {
            "from": f"Sarawak Agri-Advisor <{sender_email}>", # 严格使用配置文件中的发件人
            "to": [recipient_email],
            "subject": "Your Verification Code",
            "html": html_content,
        }

        email = resend.Emails.send(params)
        
        # Resend的成功响应中没有 status_code，我们直接检查返回的 id
        if email and email.get('id'):
            print(f"✅ Email sent via Resend to {recipient_email}, ID: {email['id']}")
            return True
        else:
            # 如果返回了非预期的内容
            print(f"❌ Resend returned an unexpected response: {email}")
            return False
        
    except Exception as e:
        # 捕获API调用时的异常，例如网络问题或Resend返回的错误
        print(f"❌ Failed to send email via Resend: {e}")
        return False