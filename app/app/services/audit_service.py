from flask import request
from flask_login import current_user

from app.context import current_company_id
from app.extensions import db
from app.models import AuditLog


def write_audit(action, table_name, record_id=None, previous_values=None, new_values=None, company_id=None):
    if not company_id and current_user.is_authenticated:
        company_id = current_company_id()

    if not company_id:
        return

    audit = AuditLog(
        company_id=company_id,
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        table_name=table_name,
        record_id=record_id,
        previous_values=previous_values,
        new_values=new_values,
        ip_address=request.remote_addr if request else None,
        user_agent=str(request.user_agent)[:500] if request else None,
    )
    db.session.add(audit)
