from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app.context import current_company_id, is_platform_admin
from app.extensions import db
from app.models import Employee, User
from app.permissions.decorators import manager_required
from app.roles import ROLE_EMPLOYEE, ROLE_SUPERVISOR
from app.services.audit_service import write_audit
from app.services.visibility_service import employee_is_visible, visible_employees_query

employees_bp = Blueprint("employees", __name__, url_prefix="/employees")


@employees_bp.route("/")
@manager_required
def index():
    employees_query = Employee.query.filter_by(company_id=current_company_id(), deleted_at=None)
    employees = visible_employees_query(employees_query).order_by(Employee.last_name).all()
    linked_user_ids = {employee.user.id for employee in employees if employee.user}
    collaborator_users = (
        User.query.filter(
            User.company_id == current_company_id(),
            User.deleted_at.is_(None),
            User.is_active_flag.is_(True),
            User.role.in_([ROLE_EMPLOYEE, ROLE_SUPERVISOR]),
        )
        .order_by(User.username)
        .all()
    )
    unlinked_users = [user for user in collaborator_users if user.id not in linked_user_ids]
    return render_template("employees/index.html", employees=employees, unlinked_users=unlinked_users)


@employees_bp.route("/create", methods=["GET", "POST"])
@manager_required
def create():
    existing_user = None
    existing_user_id = request.form.get("existing_user_id", type=int) if request.method == "POST" else request.args.get("user_id", type=int)
    if existing_user_id:
        existing_user = User.query.filter_by(
            id=existing_user_id,
            company_id=current_company_id(),
            deleted_at=None,
        ).first()
        if not existing_user:
            flash("Ese usuario ya tiene ficha de colaborador o no existe.", "danger")
            return redirect(url_for("employees.index"))

    if request.method == "POST":
        try:
            employee = existing_user.employee if existing_user and existing_user.employee else Employee(company_id=current_company_id(), created_by=current_user.id)
            employee.first_name = request.form.get("first_name", "").strip()
            employee.last_name = request.form.get("last_name", "").strip()
            employee.document_number = request.form.get("document_number", "").strip()
            employee.email = request.form.get("email", "").strip().lower() or None
            employee.phone = request.form.get("phone", "").strip() or None
            employee.position = request.form.get("position", "").strip() or None
            employee.notes = request.form.get("notes", "").strip() or None
            employee.active = True
            employee.deleted_at = None
            employee.deleted_by = None
            employee.updated_by = current_user.id
            if not employee.first_name or not employee.last_name or not employee.document_number:
                raise ValueError("Completá nombre, apellido y documento.")
            db.session.add(employee)
            db.session.flush()

            if existing_user:
                existing_user.employee_id = employee.id
                existing_user.email = employee.email or existing_user.email
                existing_user.updated_by = current_user.id
            elif request.form.get("create_user") == "on":
                username = request.form.get("username", "").strip().lower()
                password = request.form.get("password", "")
                role = request.form.get("role", ROLE_EMPLOYEE)
                if role not in (ROLE_EMPLOYEE, ROLE_SUPERVISOR):
                    role = ROLE_EMPLOYEE
                if not username or not password:
                    raise ValueError("Para crear usuario, completa usuario y clave.")
                email = employee.email or f"{username}@local"
                user = User.query.filter_by(username=username).first()
                if user and user.deleted_at is None:
                    raise ValueError("Ya existe un usuario activo con ese nombre.")
                email_owner = User.query.filter(User.email == email, User.username != username).first()
                if email_owner and email_owner.deleted_at is None:
                    raise ValueError("Ya existe un usuario activo con ese email.")
                if user:
                    user.company_id = current_company_id()
                    user.employee_id = employee.id
                    user.email = email
                    user.role = role
                    user.deleted_at = None
                    user.deleted_by = None
                    user.is_active_flag = True
                    user.is_company_owner = False
                    user.is_platform_admin = False
                    user.updated_by = current_user.id
                else:
                    user = User(
                        company_id=current_company_id(),
                        employee_id=employee.id,
                        username=username,
                        email=email,
                        role=role,
                        created_by=current_user.id,
                    )
                user.set_password(password)
                db.session.add(user)

            write_audit("CREATE", "employees", employee.id, new_values={"name": employee.full_name})
            db.session.commit()
            flash("Colaborador creado.", "success")
            return redirect(url_for("employees.index"))
        except (IntegrityError, ValueError) as exc:
            db.session.rollback()
            flash(str(getattr(exc, "orig", exc)), "danger")

    form_defaults = {
        "first_name": request.form.get("first_name", existing_user.employee.first_name if existing_user and existing_user.employee else existing_user.username if existing_user else ""),
        "last_name": request.form.get("last_name", existing_user.employee.last_name if existing_user and existing_user.employee else ""),
        "email": request.form.get("email", existing_user.employee.email if existing_user and existing_user.employee and existing_user.employee.email else existing_user.email if existing_user else ""),
        "document_number": request.form.get("document_number", existing_user.employee.document_number if existing_user and existing_user.employee else ""),
        "phone": request.form.get("phone", existing_user.employee.phone if existing_user and existing_user.employee and existing_user.employee.phone else ""),
        "position": request.form.get("position", existing_user.employee.position if existing_user and existing_user.employee and existing_user.employee.position else ""),
        "notes": request.form.get("notes", existing_user.employee.notes if existing_user and existing_user.employee and existing_user.employee.notes else ""),
    }
    return render_template("employees/form.html", employee=None, existing_user=existing_user, form_defaults=form_defaults)


@employees_bp.route("/<int:employee_id>/edit", methods=["GET", "POST"])
@manager_required
def edit(employee_id):
    employee = Employee.query.filter_by(id=employee_id, company_id=current_company_id()).first_or_404()

    if employee.user and employee.user.is_company_owner and not current_user.is_company_owner and not is_platform_admin():
        return ("Forbidden", 403)
    if not employee_is_visible(employee):
        return ("Forbidden", 403)

    if request.method == "POST":
        try:
            previous_values = {
                "first_name": employee.first_name,
                "last_name": employee.last_name,
                "document_number": employee.document_number,
                "email": employee.email,
                "phone": employee.phone,
                "position": employee.position,
            }

            employee.first_name = request.form.get("first_name", "").strip()
            employee.last_name = request.form.get("last_name", "").strip()
            employee.document_number = request.form.get("document_number", "").strip()
            employee.email = request.form.get("email", "").strip().lower() or None
            employee.phone = request.form.get("phone", "").strip() or None
            employee.position = request.form.get("position", "").strip() or None
            employee.notes = request.form.get("notes", "").strip() or None
            employee.active = True
            employee.deleted_at = None
            employee.deleted_by = None
            employee.updated_by = current_user.id

            if not employee.first_name or not employee.last_name or not employee.document_number:
                raise ValueError("Completá nombre, apellido y documento.")

            if employee.user:
                employee.user.email = employee.email or employee.user.email
                employee.user.updated_by = current_user.id
                new_password = request.form.get("password", "")
                if new_password:
                    employee.user.set_password(new_password)
                    write_audit(
                        "PASSWORD_CHANGE",
                        "users",
                        employee.user.id,
                        new_values={"employee_id": employee.id, "reset_by": current_user.id},
                    )

            write_audit(
                "UPDATE",
                "employees",
                employee.id,
                previous_values=previous_values,
                new_values={
                    "first_name": employee.first_name,
                    "last_name": employee.last_name,
                    "document_number": employee.document_number,
                    "email": employee.email,
                    "phone": employee.phone,
                    "position": employee.position,
                },
            )
            db.session.commit()
            flash("Colaborador actualizado.", "success")
            return redirect(url_for("employees.index"))
        except (IntegrityError, ValueError) as exc:
            db.session.rollback()
            flash(str(getattr(exc, "orig", exc)), "danger")

    return render_template("employees/form.html", employee=employee, existing_user=None, form_defaults=None)


@employees_bp.route("/<int:employee_id>/delete", methods=["POST"])
@manager_required
def delete(employee_id):
    employee = Employee.query.filter_by(id=employee_id, company_id=current_company_id()).first_or_404()
    if employee.user and employee.user.is_company_owner and not current_user.is_company_owner and not is_platform_admin():
        return ("Forbidden", 403)
    if not employee_is_visible(employee):
        return ("Forbidden", 403)

    employee.soft_delete(current_user.id)
    employee.active = False
    if employee.user:
        employee.user.soft_delete(current_user.id)
        employee.user.is_active_flag = False
    write_audit("DELETE", "employees", employee.id, previous_values={"name": employee.full_name})
    db.session.commit()
    flash("Colaborador eliminado lógicamente.", "success")
    return redirect(url_for("employees.index"))
