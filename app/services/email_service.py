import smtplib
from email.message import EmailMessage

from flask import current_app


def email_configured():
    return bool(current_app.config["SMTP_HOST"] and current_app.config["SMTP_FROM_EMAIL"])


def send_email(to_email, subject, body):
    if not email_configured():
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = current_app.config["SMTP_FROM_EMAIL"]
    message["To"] = to_email
    message.set_content(body)

    try:
        with smtplib.SMTP(current_app.config["SMTP_HOST"], current_app.config["SMTP_PORT"], timeout=10) as server:
            if current_app.config["SMTP_USE_TLS"]:
                server.starttls()
            if current_app.config["SMTP_USERNAME"]:
                server.login(current_app.config["SMTP_USERNAME"], current_app.config["SMTP_PASSWORD"])
            server.send_message(message)
    except (OSError, smtplib.SMTPException):
        return False
    return True
