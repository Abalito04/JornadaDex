from flask import request
from flask_login import current_user

from app.extensions import db
from app.models import SecurityEvent


def log_security_event(event_type, identifier=None, user=None, company_id=None, metadata=None):
    current = current_user if current_user.is_authenticated else None
    event_user = user or current
    event = SecurityEvent(
        event_type=event_type,
        identifier=identifier,
        user_id=event_user.id if event_user else None,
        company_id=company_id or (event_user.company_id if event_user else None),
        ip_address=request.remote_addr if request else None,
        user_agent=str(request.user_agent)[:500] if request else None,
        event_metadata=metadata,
    )
    db.session.add(event)
    db.session.commit()
