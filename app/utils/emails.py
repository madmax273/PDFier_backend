import smtplib
from email.mime.text import MIMEText
from app.core.config import settings

def send_verification_email(email: str, otp: str):
    msg = MIMEText(f"Your OTP is: {otp}")
    msg["Subject"] = "Email Verification"
    msg["From"] = settings.EMAIL_USER
    msg["To"] = email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
        server.sendmail(msg["From"], [msg["To"]], msg.as_string())
