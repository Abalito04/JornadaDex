import click
from flask.cli import with_appcontext

from app.extensions import db
from app.services.company_service import create_company_with_owner


def register_cli(app):
    app.cli.add_command(init_db)
    app.cli.add_command(create_demo)
    app.cli.add_command(create_developer)


@click.command("init-db")
@with_appcontext
def init_db():
    db.create_all()
    click.echo("Database initialized.")


@click.command("create-demo")
@with_appcontext
def create_demo():
    db.create_all()
    create_company_with_owner(
        company_name="Empresa Demo",
        tax_id="30-00000000-0",
        owner_name="Jefe Demo",
        email="jefe@demo.local",
        username="jefe",
        password="DemoAdmin123",
    )
    db.session.commit()
    click.echo("Demo created: user=jefe password=DemoAdmin123")


@click.command("create-developer")
@click.option("--username", prompt=True)
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_developer(username, email, password):
    from app.models import Company, User
    from sqlalchemy import func, or_

    db.create_all()
    company = Company.query.filter_by(name="JornadaDex Developer").first()
    legacy_company = Company.query.filter_by(name="TrazaLab Developer").first()
    if company:
        company.active = True
        company.deleted_at = None
        company.deleted_by = None
    if not company and legacy_company:
        company = legacy_company
        company.name = "JornadaDex Developer"
        company.active = True
        company.deleted_at = None
        company.deleted_by = None
    elif company and legacy_company and legacy_company.id != company.id:
        for legacy_user in User.query.filter_by(company_id=legacy_company.id).all():
            legacy_user.company_id = company.id
        legacy_company.soft_delete()
        legacy_company.active = False

    if not company:
        company = Company(name="JornadaDex Developer", active=True)
        db.session.add(company)
        db.session.flush()

    username = username.strip().lower()
    email = email.strip().lower()
    candidates = (
        User.query.filter(
            or_(
                User.username == username,
                func.lower(User.email) == email,
                User.is_platform_admin.is_(True),
                User.role == "Developer",
            )
        )
        .order_by(User.id)
        .all()
    )
    user = (
        next((candidate for candidate in candidates if candidate.username == username and candidate.deleted_at is None), None)
        or next((candidate for candidate in candidates if candidate.username == username), None)
        or next((candidate for candidate in candidates if candidate.email.lower() == email and candidate.deleted_at is None), None)
        or next((candidate for candidate in candidates if candidate.is_platform_admin and candidate.deleted_at is None), None)
        or (candidates[0] if candidates else None)
    )
    if not user:
        user = User(
            company_id=company.id,
            username=username,
            email=email,
            role="Developer",
            is_platform_admin=True,
        )
        db.session.add(user)
    user.company_id = company.id
    user.username = username
    user.email = email
    user.role = "Developer"
    user.is_platform_admin = True
    user.is_company_owner = False
    user.is_active_flag = True
    user.deleted_at = None
    user.deleted_by = None
    user.set_password(password)
    for duplicate in candidates:
        if duplicate.id == user.id:
            continue
        duplicate.is_platform_admin = False
        duplicate.is_company_owner = False
        duplicate.is_active_flag = False
        duplicate.soft_delete(user.id)
    db.session.commit()
    click.echo(f"Developer user ready: {username}")

