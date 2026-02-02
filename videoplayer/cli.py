import click
from flask.cli import with_appcontext
from sqlalchemy import func

from .extensions import db
from .models import User
from .security import hash_password

@click.command("create-user")
@click.argument("username")
@click.password_option()
@click.option("--admin", is_flag=True, default=False)
@with_appcontext
def create_user(username, password, admin):
    username = username.strip()
    exists = db.session.query(User).filter(func.lower(User.username) == username.lower()).first()
    if exists:
        raise click.ClickException("User already exists")

    u = User(username=username, password_hash=hash_password(password), is_admin=admin)
    db.session.add(u)
    db.session.commit()
    click.echo("User created")
