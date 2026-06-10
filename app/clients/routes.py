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
    return render_template("clients/form.html", client=client)


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
    return render_template("clients/form.html", client=client)


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
    flash("Cliente contable eliminado logicamente.", "success")
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
        client.active = request.form.get("active", "on") == "on"
        client.notes = request.form.get("notes", "").strip() or None

        if not client.name:
            raise ValueError("El nombre del cliente es obligatorio.")

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
                "active": client.active,
            },
        )
        db.session.commit()
        flash(success_message, "success")
        return redirect(url_for("clients.index"))
    except (IntegrityError, ValueError) as exc:
        db.session.rollback()
        flash(str(getattr(exc, "orig", exc)), "danger")
        return render_template("clients/form.html", client=client)


def _yes_no(field_name):
    return request.form.get(field_name) in {"1", "on", "true", "True", "si", "Si"}
