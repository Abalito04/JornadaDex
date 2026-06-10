from flask import Blueprint, render_template, request

from app.context import current_company_id, is_platform_admin
from app.models import AuditLog, User
from app.permissions.decorators import roles_required

audit_bp = Blueprint("audit", __name__, url_prefix="/audit")


@audit_bp.route("/")
@roles_required("Owner")
def index():
    company_id = current_company_id()
    selected_user_id = request.args.get("user_id", type=int)
    users = User.query.filter_by(company_id=company_id, deleted_at=None).order_by(User.username).all()
    selected_user = None
    events = []

    if selected_user_id:
        selected_user = User.query.filter_by(id=selected_user_id, company_id=company_id, deleted_at=None).first()
        if selected_user:
            logs = (
                AuditLog.query.filter_by(company_id=company_id, user_id=selected_user.id)
                .order_by(AuditLog.created_at.desc())
                .limit(200)
                .all()
            )
            events = [_activity_event(log) for log in logs]

    return render_template(
        "audit/index.html",
        events=events,
        users=users,
        selected_user=selected_user,
        selected_user_id=selected_user_id,
    )


def _activity_event(log):
    user = log.user.username if log.user else "Sistema"
    action = (log.action or "").upper()
    table_name = log.table_name or ""
    values = log.new_values or log.previous_values or {}
    target = _target_label(table_name)
    detail = _detail_text(values)

    action_labels = {
        "LOGIN": (f"{user} inicio sesion", "Acceso"),
        "LOGOUT": (f"{user} cerro sesion", "Acceso"),
        "CREATE": (f"{user} creo {target}", "Alta"),
        "UPDATE": (f"{user} actualizo {target}", "Cambio"),
        "DELETE": (f"{user} elimino {target}", "Baja"),
        "EXPORT": (f"{user} exporto un reporte", "Reporte"),
        "PASSWORD_CHANGE": (f"{user} cambio una clave de acceso", "Seguridad"),
    }
    title, category = action_labels.get(action, (f"{user} registro una actividad", action.title() or "Actividad"))

    return {
        "created_at": log.created_at,
        "user": user,
        "title": title,
        "category": category,
        "detail": detail,
        "icon": _icon_for(action),
        "technical": {
            "action": log.action,
            "table": log.table_name,
            "record_id": log.record_id,
            "ip": log.ip_address,
        },
        "show_technical": is_platform_admin(),
    }


def _target_label(table_name):
    labels = {
        "companies": "una empresa",
        "users": "un usuario",
        "employees": "un empleado",
        "areas": "un area",
        "tasks": "una tarea",
        "time_records": "un registro de trabajo",
        "accounting_clients": "un cliente contable",
    }
    return labels.get(table_name, "un registro")


def _detail_text(values):
    if not values:
        return "Sin detalle adicional."
    parts = []
    if values.get("name"):
        parts.append(str(values["name"]))
    if values.get("employee_id"):
        parts.append(f"Empleado #{values['employee_id']}")
    if values.get("accounting_client_id"):
        parts.append(f"Cliente #{values['accounting_client_id']}")
    if values.get("format"):
        parts.append(f"Formato {values['format']}")
    if values.get("count") is not None:
        parts.append(f"{values['count']} registros")
    if values.get("status"):
        parts.append(f"Estado {values['status']}")
    return " · ".join(parts) if parts else "Actividad registrada correctamente."


def _icon_for(action):
    icons = {
        "LOGIN": "log-in",
        "LOGOUT": "log-out",
        "CREATE": "plus",
        "UPDATE": "pencil",
        "DELETE": "trash-2",
        "EXPORT": "file-down",
        "PASSWORD_CHANGE": "key-round",
    }
    return icons.get((action or "").upper(), "activity")
