
from app import create_app
from app.extensions import db

def test_public_routes():
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, SQLALCHEMY_DATABASE_URI="sqlite://", SECRET_KEY="test-key")
    with app.app_context():
        db.create_all()
    client = app.test_client()
    for path in ["/", "/what-we-do", "/resources", "/impact", "/shop", "/contact", "/apply", "/donate", "/privacy", "/terms", "/stories", "/guide", "/faq", "/openings", "/tour", "/veterans", "/referrals", "/families", "/careers", "/partnerships", "/standards", "/policies", "/health"]:
        r = client.get(path)
        assert r.status_code in (200, 302)

def test_auth_pages():
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, SQLALCHEMY_DATABASE_URI="sqlite://", SECRET_KEY="test-key")
    with app.app_context():
        db.create_all()
    client = app.test_client()
    assert client.get("/auth/login").status_code == 200
    assert client.get("/auth/register").status_code == 200
