import os
import unittest
from datetime import datetime, timezone

os.environ.setdefault("SECRET_KEY", "test-secret-key")

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Area, Company, Employee, RateLimitEvent, SecurityEvent, Task, TimeRecord, User
from app.roles import ROLE_EMPLOYEE, ROLE_OWNER


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    PUBLIC_SIGNUP_ENABLED = True
    EMAIL_VERIFICATION_REQUIRED = False
    LOGIN_RATE_LIMIT_ATTEMPTS = 2
    SIGNUP_RATE_LIMIT_ATTEMPTS = 1


class SecurityTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self._seed()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _seed(self):
        self.company = Company(name="Empresa A", tax_id="30-1")
        self.other_company = Company(name="Empresa B", tax_id="30-2")
        db.session.add_all([self.company, self.other_company])
        db.session.flush()

        self.owner_employee = Employee(company_id=self.company.id, first_name="Owner", last_name="A", document_number="owner-a")
        self.employee = Employee(company_id=self.company.id, first_name="Empleado", last_name="A", document_number="emp-a")
        self.other_employee = Employee(company_id=self.other_company.id, first_name="Empleado", last_name="B", document_number="emp-b")
        db.session.add_all([self.owner_employee, self.employee, self.other_employee])
        db.session.flush()

        self.owner = User(company_id=self.company.id, employee_id=self.owner_employee.id, username="owner", email="owner@example.com", role=ROLE_OWNER, is_company_owner=True, email_verified_at=datetime.now(timezone.utc))
        self.owner.set_password("Owner1234")
        self.user = User(company_id=self.company.id, employee_id=self.employee.id, username="empleado", email="empleado@example.com", role=ROLE_EMPLOYEE, email_verified_at=datetime.now(timezone.utc))
        self.user.set_password("Empleado1234")
        self.other_user = User(company_id=self.other_company.id, employee_id=self.other_employee.id, username="otro", email="otro@example.com", role=ROLE_EMPLOYEE, email_verified_at=datetime.now(timezone.utc))
        self.other_user.set_password("Otro1234")
        db.session.add_all([self.owner, self.user, self.other_user])
        db.session.flush()

        self.area = Area(company_id=self.company.id, name="Area A")
        self.other_area = Area(company_id=self.other_company.id, name="Area B")
        db.session.add_all([self.area, self.other_area])
        db.session.flush()
        self.task = Task(area_id=self.area.id, name="Tarea A")
        self.other_task = Task(area_id=self.other_area.id, name="Tarea B")
        db.session.add_all([self.task, self.other_task])
        db.session.flush()

        self.owner_record = TimeRecord(company_id=self.company.id, employee_id=self.owner_employee.id, area_id=self.area.id, task_id=self.task.id, record_date=datetime.now(timezone.utc).date(), start_time=datetime.now(timezone.utc).time(), hours=0)
        self.other_record = TimeRecord(company_id=self.other_company.id, employee_id=self.other_employee.id, area_id=self.other_area.id, task_id=self.other_task.id, record_date=datetime.now(timezone.utc).date(), start_time=datetime.now(timezone.utc).time(), hours=0)
        db.session.add_all([self.owner_record, self.other_record])
        db.session.commit()

    def _login(self, username, password):
        return self.client.post("/auth/login", data={"username": username, "password": password}, follow_redirects=False)

    def test_employee_cannot_delete_another_employee_record(self):
        self._login("empleado", "Empleado1234")
        response = self.client.post(f"/time-records/{self.owner_record.id}/delete")
        self.assertEqual(response.status_code, 403)

    def test_company_record_id_cannot_cross_tenant(self):
        self._login("owner", "Owner1234")
        response = self.client.post(f"/time-records/{self.other_record.id}/delete")
        self.assertEqual(response.status_code, 404)

    def test_failed_login_records_security_event_and_rate_limit(self):
        self._login("empleado", "bad-password")
        self._login("empleado", "bad-password")
        blocked = self._login("empleado", "bad-password")
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(SecurityEvent.query.filter_by(event_type="login_failed").count(), 2)
        self.assertEqual(SecurityEvent.query.filter_by(event_type="login_rate_limited").count(), 1)
        self.assertGreaterEqual(RateLimitEvent.query.filter_by(event_type="login_failed").count(), 2)

    def test_signup_rate_limit_is_persistent(self):
        first = self.client.post(
            "/auth/signup",
            data={
                "company_name": "Empresa C",
                "tax_id": "30-3",
                "owner_name": "Owner C",
                "email": "owner-c@example.com",
                "username": "ownerc",
                "password": "OwnerC1234",
            },
            follow_redirects=False,
        )
        self.assertEqual(first.status_code, 302)
        second = self.client.post(
            "/auth/signup",
            data={
                "company_name": "Empresa D",
                "tax_id": "30-4",
                "owner_name": "Owner D",
                "email": "owner-d@example.com",
                "username": "ownerd",
                "password": "OwnerD1234",
            },
            follow_redirects=False,
        )
        self.assertEqual(second.status_code, 429)
        self.assertEqual(SecurityEvent.query.filter_by(event_type="signup_rate_limited").count(), 1)


if __name__ == "__main__":
    unittest.main()
