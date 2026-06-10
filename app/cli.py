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
        password="admin123",
    )
    db.session.commit()
    click.echo("Demo created: user=jefe password=admin123")


@click.command("create-developer")
@click.option("--username", prompt=True)
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_developer(username, email, password):
    from app.models import Company, User

    db.create_all()
    company = Company.query.filter_by(name="TrazaLab Developer").first()
    if not company:
        company = Company(name="TrazaLab Developer", active=True)
        db.session.add(company)
        db.session.flush()

    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(
            company_id=company.id,
            username=username,
            email=email,
            role="Developer",
            is_platform_admin=True,
        )
        db.session.add(user)
    user.email = email
    user.role = "Developer"
    user.is_platform_admin = True
    user.set_password(password)
    db.session.commit()
    click.echo(f"Developer user ready: {username}")
