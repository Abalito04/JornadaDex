from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app.context import current_company_id
from app.extensions import db
from app.models import AccountingClient
from app.permissions.decorators import manager_required
from app.services.audit_service import write_audit

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")


@clients_bp.route("/")
@manager_required
def index():
    clients = (
        AccountingClient.query.filter_by(company_id=current_company_id(), deleted_at=None)
        .order_by(AccountingClient.name)
        .all()
    )
    return render_template("clients/index.html", clients=clients)


@clients_bp.route("/create", methods=["GET", "POST"])
@manager_required
def create():
    client = AccountingClient(company_id=current_company_id())
    if request.method == "POST":
        return _save_client(client, "Cliente contable creado.", "CREATE")
    return _render_form(client)


@clients_bp.route("/<int:client_id>/edit", methods=["GET", "POST"])
@manager_required
def edit(client_id):
    client = AccountingClient.query.filter_by(
        id=client_id,
        company_id=current_company_id(),
        deleted_at=None,
    ).first_or_404()
    if request.method == "POST":
        return _save_client(client, "Cliente contable actualizado.", "UPDATE")
    return _render_form(client)


@clients_bp.route("/<int:client_id>/delete", methods=["POST"])
@manager_required
def delete(client_id):
    client = AccountingClient.query.filter_by(
        id=client_id,
        company_id=current_company_id(),
        deleted_at=None,
    ).first_or_404()
    client.soft_delete(current_user.id)
    client.active = False
    write_audit("DELETE", "accounting_clients", client.id, previous_values={"name": client.name})
    db.session.commit()
    flash("Cliente contable eliminado lógicamente.", "success")
    return redirect(url_for("clients.index"))


def _save_client(client, success_message, audit_action):
    try:
        previous_values = None
        if client.id:
            previous_values = {
                "name": client.name,
                "tax_id": client.tax_id,
                "address": client.address,
                "fiscal_condition": client.fiscal_condition,
                "multilateral_agreement": client.multilateral_agreement,
                "does_balance": client.does_balance,
                "sicore": client.sicore,
                "income_tax": client.income_tax,
                "personal_assets": client.personal_assets,
                "payroll_enabled": client.payroll_enabled,
                "payroll_employee_count": client.payroll_employee_count,
                "group_enabled": client.group_enabled,
                "group_name": client.group_name,
                "budgeted_hours": str(client.budgeted_hours) if client.budgeted_hours is not None else None,
                "fees": str(client.fees) if client.fees is not None else None,
                "active": client.active,
            }

        client.name = request.form.get("name", "").strip()
        client.tax_id = request.form.get("tax_id", "").strip() or None
        client.address = request.form.get("address", "").strip() or None
        client.fiscal_condition = request.form.get("fiscal_condition", "").strip() or None
        client.multilateral_agreement = request.form.get("multilateral_agreement", "").strip() or None
        client.does_balance = _yes_no("does_balance")
        client.sicore = _yes_no("sicore")
        client.income_tax = _yes_no("income_tax")
        client.personal_assets = _yes_no("personal_assets")
        client.payroll_enabled = _yes_no("payroll_enabled")
        client.payroll_employee_count = _parse_positive_int("payroll_employee_count") if client.payroll_enabled else None
        client.group_enabled = _yes_no("group_enabled")
        client.group_name = _canonical_group_name(request.form.get("group_name", "")) if client.group_enabled else None
        client.budgeted_hours = _parse_hours("budgeted_hours")
        client.fees = _parse_currency("fees")
        client.active = request.form.get("active", "on") == "on"
        client.notes = request.form.get("notes", "").strip() or None

        if not client.name:
            raise ValueError("El nombre del cliente es obligatorio.")
        if client.payroll_enabled and client.payroll_employee_count is None:
            raise ValueError("Ingresá la cantidad de empleados cuando Sueldos sea Si.")
        if client.group_enabled and not client.group_name:
            raise ValueError("Ingresá el nombre de grupo cuando Grupo sea Si.")

        if not client.id:
            client.created_by = current_user.id
            db.session.add(client)
        else:
            client.updated_by = current_user.id

        db.session.flush()
        write_audit(
            audit_action,
            "accounting_clients",
            client.id,
            previous_values=previous_values,
            new_values={
                "name": client.name,
                "tax_id": client.tax_id,
                "fiscal_condition": client.fiscal_condition,
                "does_balance": client.does_balance,
                "sicore": client.sicore,
                "income_tax": client.income_tax,
                "personal_assets": client.personal_assets,
                "payroll_enabled": client.payroll_enabled,
                "payroll_employee_count": client.payroll_employee_count,
                "group_enabled": client.group_enabled,
                "group_name": client.group_name,
                "budgeted_hours": str(client.budgeted_hours) if client.budgeted_hours is not None else None,
                "fees": str(client.fees) if client.fees is not None else None,
                "active": client.active,
            },
        )
        db.session.commit()
        flash(success_message, "success")
        return redirect(url_for("clients.index"))
    except (IntegrityError, ValueError) as exc:
        db.session.rollback()
        flash(str(getattr(exc, "orig", exc)), "danger")
        return _render_form(client)


def _yes_no(field_name):
    return request.form.get(field_name) in {"1", "on", "true", "True", "si", "Si"}


def _render_form(client):
    return render_template("clients/form.html", client=client, group_names=_group_names())


def _group_names():
    rows = (
        db.session.query(AccountingClient.group_name)
        .filter(
            AccountingClient.company_id == current_company_id(),
            AccountingClient.deleted_at.is_(None),
            AccountingClient.group_enabled.is_(True),
            AccountingClient.group_name.isnot(None),
            AccountingClient.group_name != "",
        )
        .order_by(AccountingClient.group_name)
        .all()
    )
    names = []
    seen = set()
    for (name,) in rows:
        normalized = " ".join(name.split())
        key = normalized.casefold()
        if normalized and key not in seen:
            seen.add(key)
            names.append(normalized)
    return names


def _canonical_group_name(value):
    normalized = " ".join(value.strip().split())
    if not normalized:
        return None
    for existing_name in _group_names():
        if existing_name.casefold() == normalized.casefold():
            return existing_name
    return normalized


def _parse_positive_int(field_name):
    value = request.form.get(field_name, "").strip()
    if not value:
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError("La cantidad de empleados debe ser un número entero.") from exc
    if parsed < 0:
        raise ValueError("La cantidad de empleados no puede ser negativa.")
    return parsed


def _parse_decimal(field_name):
    value = request.form.get(field_name, "").strip()
    if not value:
        return None
    if "," in value and "." in value:
        value = value.replace(".", "").replace(",", ".")
    elif "," in value:
        value = value.replace(",", ".")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Horas presupuestadas y honorarios deben ser valores numéricos.") from exc
    if parsed < 0:
        raise ValueError("Horas presupuestadas y honorarios no pueden ser negativos.")
    return parsed


def _parse_currency(field_name):
    value = request.form.get(field_name, "").strip().replace("$", "").replace(" ", "")
    if not value:
        return None
    if "," in value and "." in value:
        value = value.replace(".", "").replace(",", ".")
    elif "," in value:
        value = value.replace(",", ".")
    elif "." in value:
        value = value.replace(".", "")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Honorarios debe ser un valor numérico.") from exc
    if parsed < 0:
        raise ValueError("Honorarios no puede ser negativo.")
    return parsed


def _parse_hours(field_name):
    value = request.form.get(field_name, "").strip().lower().removesuffix("hs").strip()
    if not value:
        return None
    if ":" in value:
        hours_text, minutes_text = value.split(":", 1)
        try:
            hours = int(hours_text or 0)
            minutes = int(minutes_text or 0)
        except ValueError as exc:
            raise ValueError("Horas presupuestadas debe tener formato 00:00.") from exc
        if hours < 0 or minutes < 0 or minutes > 59:
            raise ValueError("Horas presupuestadas debe tener formato 00:00.")
        return Decimal(hours) + (Decimal(minutes) / Decimal("60"))
    return _parse_decimal(field_name)
