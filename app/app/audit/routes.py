from flask import Blueprint, render_template
from flask_login import current_user

from app.models import AuditLog
from app.permissions.decorators import roles_required

audit_bp = Blueprint("audit", __name__, url_prefix="/audit")


@audit_bp.route("/")
@roles_required("Administrator")
def index():
    logs = AuditLog.query.filter_by(company_id=current_user.company_id).order_by(AuditLog.created_at.desc()).limit(200).all()
    return render_template("audit/index.html", logs=logs)
