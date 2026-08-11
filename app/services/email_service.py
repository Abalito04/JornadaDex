import json
import smtplib
from email.message import EmailMessage
from email.utils import parseaddr
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from flask import current_app


def email_configured():
    return bool(
        current_app.config["SMTP_FROM_EMAIL"]
        and (
            current_app.config.get("BREVO_API_KEY")
            or current_app.config.get("RESEND_API_KEY")
            or current_app.config["SMTP_HOST"]
        )
    )


def _resend_api_key():
    api_key = current_app.config.get("RESEND_API_KEY")
    if api_key:
        return api_key
    if current_app.config["SMTP_HOST"] == "smtp.resend.com":
        return current_app.config["SMTP_PASSWORD"]
    return ""


def _send_resend_email(to_email, subject, body, html_body=None):
    message_payload = {
        "from": current_app.config["SMTP_FROM_EMAIL"],
        "to": [to_email],
        "subject": subject,
        "text": body,
    }
    if html_body:
        message_payload["html"] = html_body
    payload = json.dumps(message_payload).encode("utf-8")
    resend_request = urlrequest.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {_resend_api_key()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(resend_request, timeout=10) as response:
            response.read()
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        current_app.logger.warning(
            "Resend email API failed from=%s to=%s status=%s: %s",
            current_app.config["SMTP_FROM_EMAIL"],
            to_email,
            exc.code,
            details,
        )
        return False
    except (OSError, URLError) as exc:
        current_app.logger.warning(
            "Resend email API delivery failed from=%s to=%s: %s",
            current_app.config["SMTP_FROM_EMAIL"],
            to_email,
            exc,
        )
        return False
    return True


def _send_brevo_email(to_email, subject, body, html_body=None):
    sender_name, sender_email = parseaddr(current_app.config["SMTP_FROM_EMAIL"])
    sender = {"email": sender_email}
    if sender_name:
        sender["name"] = sender_name

    message_payload = {
        "sender": sender,
        "to": [{"email": to_email}],
        "subject": subject,
        "textContent": body,
    }
    if html_body:
        message_payload["htmlContent"] = html_body
    payload = json.dumps(message_payload).encode("utf-8")
    brevo_request = urlrequest.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=payload,
        headers={
            "api-key": current_app.config["BREVO_API_KEY"],
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(brevo_request, timeout=10) as response:
            response.read()
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        current_app.logger.warning(
            "Brevo email API failed from=%s to=%s status=%s: %s",
            current_app.config["SMTP_FROM_EMAIL"],
            to_email,
            exc.code,
            details,
        )
        return False
    except (OSError, URLError) as exc:
        current_app.logger.warning(
            "Brevo email API delivery failed from=%s to=%s: %s",
            current_app.config["SMTP_FROM_EMAIL"],
            to_email,
            exc,
        )
        return False
    return True


def send_email(to_email, subject, body, html_body=None):
    if not email_configured():
        current_app.logger.warning(
            "SMTP email delivery skipped because SMTP_HOST or SMTP_FROM_EMAIL is not configured."
        )
        return False
    if current_app.config.get("BREVO_API_KEY"):
        return _send_brevo_email(to_email, subject, body, html_body)
    if _resend_api_key():
        return _send_resend_email(to_email, subject, body, html_body)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = current_app.config["SMTP_FROM_EMAIL"]
    message["To"] = to_email
    message.set_content(body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

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
