from flask import Flask, request

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
        _database_checked = True

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Inicia sesion para continuar."

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.employees.routes import employees_bp
    from app.time_records.routes import time_records_bp
    from app.reports.routes import reports_bp
    from app.areas.routes import areas_bp
    from app.audit.routes import audit_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(time_records_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(areas_bp)
    app.register_blueprint(audit_bp)

    from app.cli import register_cli

    register_cli(app)
    return app
