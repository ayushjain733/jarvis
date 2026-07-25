import re
import smtplib
import random
import os
from email.mime.text import MIMEText

TRUSTED_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com"]

def is_valid_email(email: str) -> bool:
    """Validates regex and checks against trusted domains to block fake/burner emails."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        return False
    domain = email.split('@')[-1].lower()
    return domain in TRUSTED_DOMAINS

def generate_captcha():
    """Generates a simple math captcha to block basic bots."""
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    return f"What is {num1} + {num2}?", str(num1 + num2)

def send_verification_email(receiver_email: str, code: str) -> tuple[bool, str]:
    """
    Sends a 6-digit OTP code to the user.
    Returns (success_boolean, message_string)
    """
    sender = os.getenv("SMTP_EMAIL", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    
    # Detect missing or placeholder credentials
    is_placeholder = (
        not sender or 
        not password or 
        "your_email" in sender or 
        "your_app_password" in password
    )
    
    if is_placeholder:
        # Dev fallback: Show OTP directly on UI so testing isn't blocked
        return True, f"[DEV MODE] SMTP not configured in .env. Your OTP code is: {code}"

    msg = MIMEText(f"Your Jarvis Verification Code is: {code}\n\nDo not share this code with anyone.")
    msg['Subject'] = 'Jarvis OS - Email Verification Code'
    msg['From'] = sender
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        return True, "OTP successfully sent to your email!"
    except Exception as e:
        return False, f"SMTP Error: {str(e)}. Make sure you are using a 16-character Gmail App Password."