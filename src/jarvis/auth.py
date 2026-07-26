import re
import smtplib
import random
import os
import time
from email.mime.text import MIMEText

TRUSTED_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com"]
OTP_REQUEST_LOGS = {}  # Tracks email requests for rate limiting

def is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        return False
    domain = email.split('@')[-1].lower()
    return domain in TRUSTED_DOMAINS

def generate_captcha():
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    return f"What is {num1} + {num2}?", str(num1 + num2)

def check_rate_limit(email: str) -> bool:
    """Prevents email bombing by enforcing a 60-second cooldown between OTP requests."""
    current_time = time.time()
    if email in OTP_REQUEST_LOGS:
        time_passed = current_time - OTP_REQUEST_LOGS[email]
        if time_passed < 60:
            return False
    OTP_REQUEST_LOGS[email] = current_time
    return True

def send_verification_email(receiver_email: str, code: str) -> tuple[bool, str]:
    if not check_rate_limit(receiver_email):
        return False, "Please wait 60 seconds before requesting another OTP."

    sender = os.getenv("SMTP_EMAIL", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    
    is_placeholder = (not sender or not password or "your_email" in sender)
    if is_placeholder:
        return True, f"[DEV MODE] SMTP not configured. Your OTP code is: {code}"

    msg = MIMEText(f"Your Jarvis OS Verification Code is: {code}\n\nDo not share this with anyone.")
    msg['Subject'] = 'Jarvis OS - Verification'
    msg['From'] = sender
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        return True, "OTP successfully sent!"
    except Exception as e:
        return False, f"SMTP Error: {str(e)}."