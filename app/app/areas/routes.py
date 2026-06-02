from flask import Blueprint, jsonify, render_template
from flask_login import current_user, login_required

from app.models import Area, Task
from app.permissions.decorators import manager_required

areas_bp = Blueprint("areas", __name__, url_prefix="/areas")


@areas_bp.route("/")
@manager_required
def index():
    areas = Area.query.filter_by(company_id=current_user.company_id, deleted_at=None).order_by(Area.name).all()
    return render_template("areas/index.html", areas=areas)


@areas_bp.route("/<int:area_id>/tasks.json")
@login_required
def tasks_json(area_id):
    tasks = (
        Task.query.join(Area)
        .filter(Area.company_id == current_user.company_id, Area.id == area_id, Task.active.is_(True), Task.deleted_at.is_(None))
        .order_by(Task.name)
        .all()
    )
    return jsonify([{"id": task.id, "name": task.name} for task in tasks])
