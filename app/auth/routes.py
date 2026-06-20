from datetime import datetime, timezone

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User
from app.services.audit_service import write_audit
from app.services.company_service import create_company_with_owner

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

_LOGIN_FAILURES = {}


def _login_rate_key(username):
    ip_address = request.access_route[0] if request.access_route else request.remote_addr or "unknown"
    return f"{ip_address}:{username}"


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


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if not current_app.config["PUBLIC_SIGNUP_ENABLED"]:
        abort(404)
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        try:
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
            write_audit("CREATE", "companies", company.id, new_values={"name": company.name, "tax_id": company.tax_id}, company_id=company.id)
            db.session.commit()
            flash("Empresa creada. Ya podes iniciar sesion.", "success")
            return redirect(url_for("auth.login"))
        except (IntegrityError, ValueError) as exc:
            db.session.rollback()
            flash(str(getattr(exc, "orig", exc)), "danger")

    return render_template("auth/signup.html")


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
            _clear_failed_logins(username)
            user.last_login_at = datetime.now(timezone.utc)
            login_user(user)
            write_audit("LOGIN", "users", user.id, company_id=user.company_id)
            db.session.commit()
            return redirect(url_for("dashboard.index"))

        _record_failed_login(username)
        flash("Usuario o clave invalida.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    company_id = current_user.company_id
    user_id = current_user.id
    write_audit("LOGOUT", "users", user_id, company_id=company_id)
    db.session.commit()
    logout_user()
    return redirect(url_for("auth.login"))

