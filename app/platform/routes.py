from collections import defaultdict

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.context import is_platform_admin
from app.models import AccountingClient, Company, TimeRecord, User
from app.roles import ROLE_DEVELOPER, ROLE_OWNER, normalize_role
from app.services.audit_service import write_audit
from app.services.password_policy import password_strength_error

platform_bp = Blueprint("platform", __name__, url_prefix="/platform")


def require_platform_admin():
    if not is_platform_admin():
        return ("Forbidden", 403)
    return None


@platform_bp.route("/companies")
@login_required
def companies():
    denied = require_platform_admin()
    if denied:
        return denied
    companies = Company.query.filter(Company.deleted_at.is_(None)).order_by(Company.name).all()
    return render_template("platform/companies.html", companies=companies)


@platform_bp.route("/companies/create", methods=["POST"])
@login_required
def create_company():
    denied = require_platform_admin()
    if denied:
        return denied

    name = request.form.get("name", "").strip()
    tax_id = request.form.get("tax_id", "").strip() or None
    if not name:
        flash("El nombre de la empresa es obligatorio.", "danger")
        return redirect(url_for("platform.companies"))

    exists = Company.query.filter_by(name=name, deleted_at=None).first()
    if exists:
        flash("Ya existe una empresa con ese nombre.", "danger")
        return redirect(url_for("platform.companies"))

    company = Company(name=name, tax_id=tax_id, active=True)
    db.session.add(company)
    db.session.flush()
    write_audit("CREATE", "companies", company.id, new_values={"name": company.name}, company_id=company.id)
    db.session.commit()
    flash("Empresa creada.", "success")
    return redirect(url_for("platform.companies"))


@platform_bp.route("/companies/<int:company_id>/edit", methods=["GET", "POST"])
@login_required
def edit_company(company_id):
    denied = require_platform_admin()
    if denied:
        return denied

    company = Company.query.filter_by(id=company_id, deleted_at=None).first_or_404()
    if request.method == "POST":
        previous_values = {"name": company.name, "tax_id": company.tax_id, "active": company.active}
        company.name = request.form.get("name", "").strip()
        company.tax_id = request.form.get("tax_id", "").strip() or None
        company.active = request.form.get("active") == "on"
        if not company.name:
            flash("El nombre de la empresa es obligatorio.", "danger")
            return redirect(url_for("platform.edit_company", company_id=company.id))
        write_audit(
            "UPDATE",
            "companies",
            company.id,
            previous_values=previous_values,
            new_values={"name": company.name, "tax_id": company.tax_id, "active": company.active},
            company_id=company.id,
        )
        db.session.commit()
        flash("Empresa actualizada.", "success")
        return redirect(url_for("platform.companies"))

    return render_template("platform/company_form.html", company=company)


@platform_bp.route("/companies/<int:company_id>/delete", methods=["POST"])
@login_required
def delete_company(company_id):
    denied = require_platform_admin()
    if denied:
        return denied

    company = Company.query.filter_by(id=company_id, deleted_at=None).first_or_404()
    company.soft_delete()
    company.active = False
    write_audit("DELETE", "companies", company.id, previous_values={"name": company.name}, company_id=company.id)
    db.session.commit()
    if session.get("active_company_id") == company.id:
        session.pop("active_company_id", None)
    flash("Empresa eliminada lógicamente.", "success")
    return redirect(url_for("platform.companies"))


@platform_bp.route("/companies/<int:company_id>/reset-activity", methods=["POST"])
@login_required
def reset_company_activity(company_id):
    denied = require_platform_admin()
    if denied:
        return denied

    company = Company.query.filter_by(id=company_id, deleted_at=None).first_or_404()
    records = TimeRecord.query.filter_by(company_id=company.id, deleted_at=None).all()
    clients = AccountingClient.query.filter_by(company_id=company.id, deleted_at=None).all()
    for record in records:
        record.soft_delete(current_user.id)
    for client in clients:
        client.soft_delete(current_user.id)
        client.active = False
    write_audit(
        "RESET_ACTIVITY",
        "companies",
        company.id,
        previous_values={"time_records": len(records), "clients": len(clients)},
        new_values={"preserved": "company, users, collaborators, areas, tasks"},
        company_id=company.id,
    )
    db.session.commit()
    flash(
        f"Actividad reiniciada. Se conservaron empresa, usuarios y colaboradores. "
        f"Registros archivados: {len(records)}. Clientes archivados: {len(clients)}.",
        "success",
    )
    return redirect(url_for("platform.companies"))


@platform_bp.route("/users")
@login_required
def users():
    denied = require_platform_admin()
    if denied:
        return denied
    companies = Company.query.filter(Company.deleted_at.is_(None)).order_by(Company.name).all()
    users = (
        User.query.filter(User.deleted_at.is_(None))
        .join(Company, User.company_id == Company.id)
        .filter(Company.deleted_at.is_(None))
        .order_by(Company.name, User.username)
        .all()
    )
    users_by_company = defaultdict(list)
    for user in users:
        users_by_company[user.company_id].append(user)

    company_groups = [
        {
            "company": company,
            "users": users_by_company.get(company.id, []),
        }
        for company in companies
    ]
    return render_template("platform/users.html", company_groups=company_groups)


@platform_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    denied = require_platform_admin()
    if denied:
        return denied

    user = User.query.filter_by(id=user_id, deleted_at=None).first_or_404()
    companies = Company.query.filter(Company.deleted_at.is_(None)).order_by(Company.name).all()
    if request.method == "POST":
        previous_values = {
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "company_id": user.company_id,
            "is_active": user.is_active_flag,
            "is_company_owner": user.is_company_owner,
            "is_platform_admin": user.is_platform_admin,
        }
        user.username = request.form.get("username", "").strip().lower()
        user.email = request.form.get("email", "").strip().lower()
        user.role = normalize_role(request.form.get("role", "Employee"), allow_developer=True)
        user.company_id = int(request.form.get("company_id") or user.company_id)
        user.is_active_flag = request.form.get("is_active") == "on"
        user.is_platform_admin = user.role == ROLE_DEVELOPER
        user.is_company_owner = user.role == ROLE_OWNER and not user.is_platform_admin
        password = request.form.get("password", "")
        if password:
            password_error = password_strength_error(password)
            if password_error:
                flash(password_error, "danger")
                return redirect(url_for("platform.edit_user", user_id=user.id))
            user.set_password(password)
            write_audit("PASSWORD_CHANGE", "users", user.id, new_values={"reset_by": "Developer"})
        if not user.username or not user.email:
            flash("Usuario y email son obligatorios.", "danger")
            return redirect(url_for("platform.edit_user", user_id=user.id))
        write_audit(
            "UPDATE",
            "users",
            user.id,
            previous_values=previous_values,
            new_values={
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "company_id": user.company_id,
                "is_active": user.is_active_flag,
                "is_company_owner": user.is_company_owner,
                "is_platform_admin": user.is_platform_admin,
            },
            company_id=user.company_id,
        )
        db.session.commit()
        flash("Usuario actualizado.", "success")
        return redirect(url_for("platform.users"))

    return render_template("platform/user_form.html", user=user, companies=companies)


@platform_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    denied = require_platform_admin()
    if denied:
        return denied

    user = User.query.filter_by(id=user_id, deleted_at=None).first_or_404()
    if user.id == current_user.id:
        flash("No podés eliminar tu propio usuario Developer.", "danger")
        return redirect(url_for("platform.users"))

    previous_values = {
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "company_id": user.company_id,
        "is_company_owner": user.is_company_owner,
        "is_platform_admin": user.is_platform_admin,
    }
    user.soft_delete(current_user.id)
    user.is_active_flag = False
    write_audit("DELETE", "users", user.id, previous_values=previous_values, company_id=user.company_id)
    db.session.commit()
    flash("Usuario eliminado lógicamente.", "success")
    return redirect(url_for("platform.users"))


@platform_bp.route("/companies/<int:company_id>/select", methods=["POST"])
@login_required
def select_company(company_id):
    denied = require_platform_admin()
    if denied:
        return denied
    company = Company.query.filter_by(id=company_id, deleted_at=None).first_or_404()
    session["active_company_id"] = company.id
    flash(f"Empresa activa: {company.name}", "success")
    return redirect(url_for("platform.companies"))



