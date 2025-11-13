import resend
from app.config import settings

if settings.RESEND_API_KEY:
    resend.api_key = settings.RESEND_API_KEY
else:
    print("WARNING: RESEND_API_KEY is not set. Email functionality will be disabled.")

def send_verification_email(recipient_email: str, code: str) -> bool:
    if not resend.api_key:
        return False

    sender_email = settings.SENDER_EMAIL
    
    print(f"--- Preparing to send email via Resend ---")
    print(f"    FROM: {sender_email}")
    print(f"    TO: {recipient_email}")
    print(f"------------------------------------")

    html_content = f"""
    <html><body><p>Your verification code is: <b>{code}</b></p></body></html>
    """

    try:
        params = {
            "from": f"Sarawak Agri-Advisor <{sender_email}>",
            "to": [recipient_email],
            "subject": "Your Verification Code",
            "html": html_content,
        }
        email = resend.Emails.send(params)
        
        if email and email.get('id'):
            print(f"✅ Email sent via Resend to {recipient_email}, ID: {email['id']}")
            return True
        else:
            print(f"❌ Resend returned an unexpected response: {email}")
            return False
    except Exception as e:
        print(f"❌ Failed to send email via Resend: {e}")
        return False