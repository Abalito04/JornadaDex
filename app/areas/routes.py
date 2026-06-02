from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Area, Task
from app.permissions.decorators import manager_required
from app.services.audit_service import write_audit

areas_bp = Blueprint("areas", __name__, url_prefix="/areas")


@areas_bp.route("/")
@manager_required
def index():
    areas = Area.query.filter_by(company_id=current_user.company_id, deleted_at=None).order_by(Area.name).all()
    return render_template("areas/index.html", areas=areas)


@areas_bp.route("/create", methods=["POST"])
@manager_required
def create_area():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip() or None
    if not name:
        flash("El nombre del area es obligatorio.", "danger")
        return redirect(url_for("areas.index"))

    exists = Area.query.filter_by(company_id=current_user.company_id, name=name, deleted_at=None).first()
    if exists:
        flash("Ya existe un area con ese nombre.", "danger")
        return redirect(url_for("areas.index"))

    area = Area(company_id=current_user.company_id, name=name, description=description, created_by=current_user.id)
    db.session.add(area)
    db.session.flush()
    write_audit("CREATE", "areas", area.id, new_values={"name": area.name})
    db.session.commit()
    flash("Area creada.", "success")
    return redirect(url_for("areas.index"))


@areas_bp.route("/<int:area_id>/tasks/create", methods=["POST"])
@manager_required
def create_task(area_id):
    area = Area.query.filter_by(id=area_id, company_id=current_user.company_id, deleted_at=None).first_or_404()
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip() or None
    if not name:
        flash("El nombre de la tarea es obligatorio.", "danger")
        return redirect(url_for("areas.index"))

    exists = Task.query.filter_by(area_id=area.id, name=name, deleted_at=None).first()
    if exists:
        flash("Ya existe una tarea con ese nombre en el area.", "danger")
        return redirect(url_for("areas.index"))

    task = Task(area_id=area.id, name=name, description=description, created_by=current_user.id)
    db.session.add(task)
    db.session.flush()
    write_audit("CREATE", "tasks", task.id, new_values={"area_id": area.id, "name": task.name})
    db.session.commit()
    flash("Tarea creada.", "success")
    return redirect(url_for("areas.index"))


@areas_bp.route("/<int:area_id>/delete", methods=["POST"])
@manager_required
def delete_area(area_id):
    area = Area.query.filter_by(id=area_id, company_id=current_user.company_id, deleted_at=None).first_or_404()
    area.soft_delete(current_user.id)
    area.active = False
    for task in area.tasks:
        if not task.deleted_at:
            task.soft_delete(current_user.id)
            task.active = False
    write_audit("DELETE", "areas", area.id, previous_values={"name": area.name})
    db.session.commit()
    flash("Area eliminada logicamente junto con sus tareas.", "success")
    return redirect(url_for("areas.index"))


@areas_bp.route("/tasks/<int:task_id>/delete", methods=["POST"])
@manager_required
def delete_task(task_id):
    task = (
        Task.query.join(Area)
        .filter(Task.id == task_id, Area.company_id == current_user.company_id, Task.deleted_at.is_(None))
        .first_or_404()
    )
    task.soft_delete(current_user.id)
    task.active = False
    write_audit("DELETE", "tasks", task.id, previous_values={"name": task.name})
    db.session.commit()
    flash("Tarea eliminada logicamente.", "success")
    return redirect(url_for("areas.index"))


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
