import os

from flask import Flask, request
from sqlalchemy import inspect, text

from app.config import Config
from app.extensions import csrf, db, login_manager, migrate

_database_checked = False


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    @app.before_request
    def ensure_database():
        global _database_checked
        if _database_checked or request.endpoint == "healthz" or request.path.startswith("/static/"):
            return

        with app.app_context():
            db.create_all()
            ensure_runtime_schema()
            bootstrap_platform_admin()
        _database_checked = True

    login_manager.login_view = "auth.login"
    login_manager.login_message = None

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.employees.routes import employees_bp
    from app.clients.routes import clients_bp
    from app.time_records.routes import time_records_bp
    from app.reports.routes import reports_bp
    from app.areas.routes import areas_bp
    from app.audit.routes import audit_bp
    from app.platform.routes import platform_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(time_records_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(areas_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(platform_bp)

    @app.context_processor
    def inject_global_context():
        from app.context import current_company, is_platform_admin
        from app.roles import role_label
        from app.utils.datetime import format_datetime_argentina, format_duration_hs, format_time_hs

        return {
            "active_company": current_company,
            "is_platform_admin": is_platform_admin,
            "role_label": role_label,
            "format_time_hs": format_time_hs,
            "format_duration_hs": format_duration_hs,
            "format_datetime_argentina": format_datetime_argentina,
        }

    from app.cli import register_cli

    register_cli(app)
    return app


def ensure_runtime_schema():
    inspector = inspect(db.engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "is_platform_admin" not in columns:
        db.session.execute(text("ALTER TABLE users ADD COLUMN is_platform_admin BOOLEAN NOT NULL DEFAULT FALSE"))
        db.session.commit()
    db.session.execute(text("UPDATE users SET role = 'Owner', is_company_owner = TRUE WHERE role = 'Administrator'"))
    db.session.commit()
    if "employees" in inspector.get_table_names():
        db.session.execute(
            text(
                "UPDATE users SET role = 'Supervisor', is_company_owner = FALSE "
                "WHERE is_platform_admin = FALSE "
                "AND id IN ("
                "  SELECT users.id FROM users "
                "  JOIN employees ON users.employee_id = employees.id "
                "  WHERE LOWER(COALESCE(employees.position, '')) LIKE '%supervisor%' "
                "  AND LOWER(COALESCE(employees.document_number, '')) NOT LIKE 'owner-%'"
                ")"
            )
        )
        db.session.commit()

    if "time_records" in inspector.get_table_names():
        time_record_columns = {column["name"] for column in inspector.get_columns("time_records")}
        if "accounting_client_id" not in time_record_columns:
            db.session.execute(text("ALTER TABLE time_records ADD COLUMN accounting_client_id INTEGER"))
            db.session.commit()
        if "supervisor_id" not in time_record_columns:
            db.session.execute(text("ALTER TABLE time_records ADD COLUMN supervisor_id INTEGER"))
            db.session.commit()

    if "accounting_clients" in inspector.get_table_names():
        client_columns = {column["name"] for column in inspector.get_columns("accounting_clients")}
        for column_name in ("sicore", "income_tax", "personal_assets"):
            if column_name not in client_columns:
                db.session.execute(text(f"ALTER TABLE accounting_clients ADD COLUMN {column_name} BOOLEAN NOT NULL DEFAULT FALSE"))
        db.session.commit()


def bootstrap_platform_admin():
    from app.config import clean_env_value

    username = clean_env_value(os.getenv("DEVELOPER_USERNAME"))
    password = clean_env_value(os.getenv("DEVELOPER_PASSWORD"))
    email = clean_env_value(os.getenv("DEVELOPER_EMAIL")) or "developer@trazalab.local"
    if not username or not password:
        return
    username = username.strip().lower()
    email = email.strip().lower()

    from app.models import Company, User

    user = User.query.filter_by(username=username).first()
    if user:
        user.email = email
        user.is_platform_admin = True
        user.role = "Developer"
        user.is_active_flag = True
        user.deleted_at = None
        user.set_password(password)
        db.session.commit()
        return

    company = Company.query.filter_by(name="TrazaLab Developer").first()
    if not company:
        company = Company(name="TrazaLab Developer", active=True)
        db.session.add(company)
        db.session.flush()

    developer = User(
        company_id=company.id,
        username=username,
        email=email,
        role="Developer",
        is_company_owner=False,
    )
    developer.is_platform_admin = True
    developer.set_password(password)
    db.session.add(developer)
    db.session.commit()
