import click
from flask.cli import with_appcontext

from app.extensions import db
from app.services.company_service import create_company_with_owner


def register_cli(app):
    app.cli.add_command(init_db)
    app.cli.add_command(create_demo)


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
        owner_name="Jefe Demo",
        email="jefe@demo.local",
        username="jefe",
        password="admin123",
    )
    db.session.commit()
    click.echo("Demo created: user=jefe password=admin123")
