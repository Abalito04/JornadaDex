from app.extensions import db
from app.models import Area, Company, Task
from app.roles import ROLE_OWNER
from app.seed_data import INITIAL_DEFINITION


def seed_company_catalog(company_id, user_id=None):
    for area_name, tasks in INITIAL_DEFINITION.items():
        area = Area(company_id=company_id, name=area_name, created_by=user_id)
        db.session.add(area)
        db.session.flush()
        for task_name in tasks:
            db.session.add(Task(area_id=area.id, name=task_name, created_by=user_id))


def create_company_with_owner(company_name, tax_id, owner_name, email, username, password):
    from app.models import Employee, User

    company = Company(name=company_name, tax_id=tax_id)
    db.session.add(company)
    db.session.flush()

    parts = owner_name.strip().split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else "Jefe"
    employee = Employee(
        company_id=company.id,
        first_name=first_name,
        last_name=last_name,
        document_number=f"owner-{company.id}",
        email=email,
        position="Jefe",
        created_by=None,
    )
    db.session.add(employee)
    db.session.flush()

    user = User(
        company_id=company.id,
        employee_id=employee.id,
        username=username,
        email=email,
        role=ROLE_OWNER,
        is_company_owner=True,
        created_by=None,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    company.created_by = user.id
    employee.created_by = user.id
    user.created_by = user.id
    seed_company_catalog(company.id, user.id)
    return company, user
