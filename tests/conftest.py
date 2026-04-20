"""Shared pytest fixtures for the overcomers test suite."""

from __future__ import annotations

import pytest

from app import create_app
from app.extensions import db as _db
from app.models import User


@pytest.fixture
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI="sqlite://",
        SECRET_KEY="test-key",
        RATELIMIT_ENABLED=False,
        SERVER_NAME="localhost.test",
    )
    with app.app_context():
        _db.drop_all()
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db


def make_user(db, *, email="alice@test.com", username="alice", password="password123",
               name="Alice", is_admin=False, is_moderator=False, email_confirmed=True):
    user = User(name=name, username=username, email=email,
                email_confirmed=email_confirmed, is_admin=is_admin, is_moderator=is_moderator)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def login(client, identifier, password="password123"):
    return client.post(
        "/auth/login",
        data={"identifier": identifier, "password": password},
        follow_redirects=False,
    )
