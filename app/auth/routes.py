from datetime import datetime, timezone
import json
from urllib import parse, request as urlrequest
from urllib.error import URLError

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User
from app.services.audit_service import write_audit
from app.services.company_service import create_company_with_owner
from app.services.email_service import send_email
from app.services.password_policy import validate_password_strength
from app.services.token_service import create_security_token, load_security_token

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

_LOGIN_FAILURES = {}
_SIGNUP_ATTEMPTS = {}


def _client_ip():
    return request.access_route[0] if request.access_route else request.remote_addr or "unknown"


def _login_rate_key(username):
    return f"{_client_ip()}:{username}"


def _is_login_limited(username):
    key = _login_rate_key(username)
    window = current_app.config["LOGIN_RATE_LIMIT_WINDOW"]
    max_attempts = current_app.config["LOGIN_RATE_LIMIT_ATTEMPTS"]
    now = datetime.now(timezone.utc)
    attempts = [attempt for attempt in _LOGIN_FAILURES.get(key, []) if now - attempt < window]
    _LOGIN_FAILURES[key] = attempts
    return len(attempts) >= max_attempts


def _record_failed_login(username):
    key = _login_rate_key(username)
    attempts = _LOGIN_FAILURES.setdefault(key, [])
    attempts.append(datetime.now(timezone.utc))


def _clear_failed_logins(username):
    _LOGIN_FAILURES.pop(_login_rate_key(username), None)


def _is_signup_limited():
    key = _client_ip()
    window = current_app.config["SIGNUP_RATE_LIMIT_WINDOW"]
    max_attempts = current_app.config["SIGNUP_RATE_LIMIT_ATTEMPTS"]
    now = datetime.now(timezone.utc)
    attempts = [attempt for attempt in _SIGNUP_ATTEMPTS.get(key, []) if now - attempt < window]
    _SIGNUP_ATTEMPTS[key] = attempts
    return len(attempts) >= max_attempts


def _record_signup_attempt():
    attempts = _SIGNUP_ATTEMPTS.setdefault(_client_ip(), [])
    attempts.append(datetime.now(timezone.utc))


def _turnstile_configured():
    site_key = current_app.config["TURNSTILE_SITE_KEY"]
    secret_key = current_app.config["TURNSTILE_SECRET_KEY"]
    if bool(site_key) != bool(secret_key):
        raise RuntimeError("TURNSTILE_SITE_KEY and TURNSTILE_SECRET_KEY must be configured together.")
    return bool(site_key and secret_key)


def _verify_turnstile():
    if not _turnstile_configured():
        return True

    token = request.form.get("cf-turnstile-response", "")
    if not token:
        return False

    payload = parse.urlencode(
        {
            "secret": current_app.config["TURNSTILE_SECRET_KEY"],
            "response": token,
            "remoteip": request.remote_addr or "",
        }
    ).encode("utf-8")
    verification_request = urlrequest.Request(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urlrequest.urlopen(verification_request, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, ValueError):
        return False
    return bool(result.get("success"))


def _email_verification_required(user):
    return bool(
        current_app.config["EMAIL_VERIFICATION_REQUIRED"]
        and user
        and not user.is_platform_admin
        and user.email_verified_at is None
    )


def _send_verification_email(user):
    max_age_hours = current_app.config["EMAIL_VERIFICATION_MAX_AGE_HOURS"]
    token = create_security_token("email-verify", {"user_id": user.id, "email": user.email})
    verify_url = url_for("auth.verify_email", token=token, _external=True)
    body = (
        "Hola,\n\n"
        "Confirma tu email para activar tu cuenta de JornadaDex:\n"
        f"{verify_url}\n\n"
        f"Este enlace vence en {max_age_hours} horas.\n\n"
        "Si no solicitaste esta cuenta, podes ignorar este mensaje."
    )
    return send_email(user.email, "Confirma tu email en JornadaDex", body)


def _send_password_reset_email(user):
    max_age_minutes = current_app.config["PASSWORD_RESET_MAX_AGE_MINUTES"]
    token = create_security_token(
        "password-reset",
        {"user_id": user.id, "email": user.email, "password_hash": user.password_hash},
    )
    reset_url = url_for("auth.reset_password", token=token, _external=True)
    body = (
        "Hola,\n\n"
        "Recibimos una solicitud para restablecer tu clave de JornadaDex:\n"
        f"{reset_url}\n\n"
        f"Este enlace vence en {max_age_minutes} minutos y se invalida al cambiar la clave.\n\n"
        "Si no fuiste vos, podes ignorar este mensaje."
    )
    return send_email(user.email, "Restablece tu clave de JornadaDex", body)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if not current_app.config["PUBLIC_SIGNUP_ENABLED"]:
        abort(404)
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        try:
            if _is_signup_limited():
                flash("Demasiadas altas desde esta red. Proba de nuevo mas tarde.", "danger")
                return render_template("auth/signup.html"), 429
            _record_signup_attempt()

            if not _verify_turnstile():
                raise ValueError("No pudimos validar el captcha. Intentalo nuevamente.")

            company, user = create_company_with_owner(
                company_name=request.form.get("company_name", "").strip(),
                tax_id=request.form.get("tax_id", "").strip(),
                owner_name=request.form.get("owner_name", "").strip(),
                email=request.form.get("email", "").strip().lower(),
                username=request.form.get("username", "").strip().lower(),
                password=request.form.get("password", ""),
            )
            if not company.name or not company.tax_id or not user.email or not user.username or not request.form.get("password"):
                raise ValueError("Completa nombre de la empresa, CUIT, administrador, email, usuario y clave.")
            if not current_app.config["EMAIL_VERIFICATION_REQUIRED"]:
                user.email_verified_at = datetime.now(timezone.utc)
            write_audit("CREATE", "companies", company.id, new_values={"name": company.name, "tax_id": company.tax_id}, company_id=company.id)
            db.session.commit()
            if current_app.config["EMAIL_VERIFICATION_REQUIRED"]:
                sent = _send_verification_email(user)
                if sent:
                    flash("Empresa creada. Te enviamos un email para activar la cuenta.", "success")
                else:
                    flash("Empresa creada, pero no pudimos enviar el email de activacion. Contacta soporte.", "warning")
            else:
                flash("Empresa creada. Ya podes iniciar sesion.", "success")
            return redirect(url_for("auth.login"))
        except (IntegrityError, ValueError) as exc:
            db.session.rollback()
            flash(str(getattr(exc, "orig", exc)), "danger")

    return render_template("auth/signup.html")


@auth_bp.route("/verify-email/<token>")
def verify_email(token):
    max_age_seconds = current_app.config["EMAIL_VERIFICATION_MAX_AGE_HOURS"] * 3600
    payload = load_security_token("email-verify", token, max_age_seconds)
    if not payload:
        flash("El enlace de verificacion vencio o no es valido.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(id=payload.get("user_id"), deleted_at=None).first()
    if not user or user.email != payload.get("email"):
        flash("El enlace de verificacion no es valido.", "danger")
        return redirect(url_for("auth.login"))

    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(timezone.utc)
        write_audit("EMAIL_VERIFY", "users", user.id, company_id=user.company_id)
        db.session.commit()
    flash("Email verificado. Ya podes iniciar sesion.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        if _is_login_limited(username):
            flash("Demasiados intentos fallidos. Proba de nuevo en unos minutos.", "danger")
            return render_template("auth/login.html"), 429

        user = User.query.filter(User.username == username, User.deleted_at.is_(None)).first()
        if user and user.check_password(password) and user.is_active:
            if _email_verification_required(user):
                sent = _send_verification_email(user)
                if sent:
                    flash("Antes de ingresar tenes que verificar tu email. Te enviamos un nuevo enlace.", "warning")
                else:
                    flash("Tu email no esta verificado y no pudimos enviar el enlace. Contacta soporte.", "danger")
                return render_template("auth/login.html"), 403
            _clear_failed_logins(username)
            user.last_login_at = datetime.now(timezone.utc)
            login_user(user)
            write_audit("LOGIN", "users", user.id, company_id=user.company_id)
            db.session.commit()
            return redirect(url_for("dashboard.index"))

        _record_failed_login(username)
        flash("Usuario o clave invalida.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/password-reset", methods=["GET", "POST"])
def request_password_reset():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        user = User.query.filter(
            User.deleted_at.is_(None),
            User.is_active_flag.is_(True),
            or_(User.username == identifier, User.email == identifier),
        ).first()
        if user:
            _send_password_reset_email(user)
            write_audit("PASSWORD_RESET_REQUEST", "users", user.id, company_id=user.company_id)
            db.session.commit()
        flash("Si existe una cuenta activa con esos datos, te enviamos un enlace para restablecer la clave.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/password_reset_request.html")


@auth_bp.route("/password-reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    max_age_seconds = current_app.config["PASSWORD_RESET_MAX_AGE_MINUTES"] * 60
    payload = load_security_token("password-reset", token, max_age_seconds)
    user = None
    if payload:
        user = User.query.filter_by(id=payload.get("user_id"), deleted_at=None).first()
    if not user or user.email != payload.get("email") or user.password_hash != payload.get("password_hash"):
        flash("El enlace para restablecer la clave vencio o no es valido.", "danger")
        return redirect(url_for("auth.request_password_reset"))

    if request.method == "POST":
        try:
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            if password != confirm_password:
                raise ValueError("Las claves no coinciden.")
            validate_password_strength(password)
            user.set_password(password)
            user.email_verified_at = user.email_verified_at or datetime.now(timezone.utc)
            write_audit("PASSWORD_RESET", "users", user.id, company_id=user.company_id)
            db.session.commit()
            flash("Clave actualizada. Ya podes iniciar sesion.", "success")
            return redirect(url_for("auth.login"))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    return render_template("auth/password_reset.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    company_id = current_user.company_id
    user_id = current_user.id
    write_audit("LOGOUT", "users", user_id, company_id=company_id)
    db.session.commit()
    logout_user()
    return redirect(url_for("auth.login"))

