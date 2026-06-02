from flask import Blueprint, flash, redirect, render_template, session, url_for
from flask_login import login_required

from app.context import is_platform_admin
from app.models import Company

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


@platform_bp.route("/companies/<int:company_id>/select", methods=["POST"])
@login_required
def select_company(company_id):
    denied = require_platform_admin()
    if denied:
        return denied
    company = Company.query.filter_by(id=company_id, deleted_at=None).first_or_404()
    session["active_company_id"] = company.id
    flash(f"Empresa activa: {company.name}", "success")
    return redirect(url_for("dashboard.index"))
