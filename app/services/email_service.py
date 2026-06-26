import smtplib
from email.message import EmailMessage

from flask import current_app


def email_configured():
    return bool(current_app.config["SMTP_HOST"] and current_app.config["SMTP_FROM_EMAIL"])


def send_email(to_email, subject, body):
    if not email_configured():
        current_app.logger.warning(
            "SMTP email delivery skipped because SMTP_HOST or SMTP_FROM_EMAIL is not configured."
        )
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
    except smtplib.SMTPAuthenticationError as exc:
        current_app.logger.warning(
            "SMTP authentication failed for host=%s port=%s username=%s: %s",
            current_app.config["SMTP_HOST"],
            current_app.config["SMTP_PORT"],
            current_app.config["SMTP_USERNAME"] or "<empty>",
            exc,
        )
        return False
    except smtplib.SMTPSenderRefused as exc:
        current_app.logger.warning(
            "SMTP sender refused from=%s to=%s host=%s: %s",
            current_app.config["SMTP_FROM_EMAIL"],
            to_email,
            current_app.config["SMTP_HOST"],
            exc,
        )
        return False
    except smtplib.SMTPRecipientsRefused as exc:
        current_app.logger.warning(
            "SMTP recipient refused to=%s host=%s: %s",
            to_email,
            current_app.config["SMTP_HOST"],
            exc,
        )
        return False
    except (OSError, smtplib.SMTPException) as exc:
        current_app.logger.warning(
            "SMTP email delivery failed from=%s to=%s host=%s port=%s use_tls=%s: %s",
            current_app.config["SMTP_FROM_EMAIL"],
            to_email,
            current_app.config["SMTP_HOST"],
            current_app.config["SMTP_PORT"],
            current_app.config["SMTP_USE_TLS"],
            exc,
        )
        return False
    return True
