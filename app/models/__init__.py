from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class AuditMixin:
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    deleted_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self, user_id=None):
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = user_id


class Company(db.Model, AuditMixin):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    tax_id = db.Column(db.String(50), nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)

    users = db.relationship("User", back_populates="company", foreign_keys="User.company_id")
    employees = db.relationship("Employee", back_populates="company")
    areas = db.relationship("Area", back_populates="company")
    accounting_clients = db.relationship("AccountingClient", back_populates="company")


class User(UserMixin, db.Model, AuditMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="Employee")
    is_company_owner = db.Column(db.Boolean, default=False, nullable=False)
    is_platform_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active_flag = db.Column(db.Boolean, default=True, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)

    company = db.relationship("Company", back_populates="users", foreign_keys=[company_id])
    employee = db.relationship("Employee", back_populates="user", foreign_keys=[employee_id])

    @property
    def is_active(self):
        return self.is_active_flag and self.deleted_at is None

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Employee(db.Model, AuditMixin):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    document_number = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(60), nullable=True)
    position = db.Column(db.String(120), nullable=True)
    hire_date = db.Column(db.Date, nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    company = db.relationship("Company", back_populates="employees")
    user = db.relationship("User", back_populates="employee", uselist=False, foreign_keys="User.employee_id")
    time_records = db.relationship("TimeRecord", back_populates="employee")

    __table_args__ = (
        db.UniqueConstraint("company_id", "document_number", name="uq_employee_document_company"),
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class Area(db.Model, AuditMixin):
    __tablename__ = "areas"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)

    company = db.relationship("Company", back_populates="areas")
    tasks = db.relationship("Task", back_populates="area")

    __table_args__ = (db.UniqueConstraint("company_id", "name", name="uq_area_company"),)


class Task(db.Model, AuditMixin):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    area_id = db.Column(db.Integer, db.ForeignKey("areas.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)

    area = db.relationship("Area", back_populates="tasks")
    time_records = db.relationship("TimeRecord", back_populates="task")

    __table_args__ = (db.UniqueConstraint("area_id", "name", name="uq_task_area"),)


class AccountingClient(db.Model, AuditMixin):
    __tablename__ = "accounting_clients"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    name = db.Column(db.String(180), nullable=False)
    tax_id = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    fiscal_condition = db.Column(db.String(120), nullable=True)
    multilateral_agreement = db.Column(db.String(120), nullable=True)
    does_balance = db.Column(db.Boolean, default=False, nullable=False)
    sicore = db.Column(db.Boolean, default=False, nullable=False)
    income_tax = db.Column(db.Boolean, default=False, nullable=False)
    personal_assets = db.Column(db.Boolean, default=False, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    company = db.relationship("Company", back_populates="accounting_clients")
    time_records = db.relationship("TimeRecord", back_populates="accounting_client")

    __table_args__ = (db.UniqueConstraint("company_id", "name", name="uq_accounting_client_company"),)


class TimeRecord(db.Model, AuditMixin):
    __tablename__ = "time_records"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    accounting_client_id = db.Column(db.Integer, db.ForeignKey("accounting_clients.id"), nullable=True)
    area_id = db.Column(db.Integer, db.ForeignKey("areas.id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    record_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=True)
    hours = db.Column(db.Numeric(8, 2), nullable=False, default=0)
    observations = db.Column(db.Text, nullable=True)

    employee = db.relationship("Employee", back_populates="time_records")
    supervisor = db.relationship("User", foreign_keys=[supervisor_id])
    accounting_client = db.relationship("AccountingClient", back_populates="time_records")
    area = db.relationship("Area")
    task = db.relationship("Task", back_populates="time_records")


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    table_name = db.Column(db.String(120), nullable=False)
    record_id = db.Column(db.Integer, nullable=True)
    previous_values = db.Column(db.JSON, nullable=True)
    new_values = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User", foreign_keys=[user_id])
