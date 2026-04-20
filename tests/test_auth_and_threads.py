"""Focused tests for auth, role gates, password reset, and thread moderation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.extensions import db as _db
from app.models import Event, EventPost, EventRSVP, Opening, OpeningPost, User

from .conftest import login, make_user


# ── Auth ───────────────────────────────────────────────────────

def test_register_then_login(client, db):
    r = client.post("/auth/register", data={
        "name": "Bob", "email": "bob@test.com", "username": "bob",
        "password": "password123",
    }, follow_redirects=True)
    assert r.status_code == 200
    user = User.query.filter_by(email="bob@test.com").first()
    assert user is not None

    r = login(client, "bob")
    assert r.status_code in (302, 303)


def test_login_wrong_password_401(client, db):
    make_user(db)
    r = login(client, "alice", password="wrong-password")
    assert r.status_code == 401


def test_register_duplicate_email_rejected(client, db):
    make_user(db, email="dup@test.com", username="first")
    r = client.post("/auth/register", data={
        "name": "Second", "email": "dup@test.com", "username": "second",
        "password": "password123",
    })
    assert r.status_code == 409


# ── Password reset ─────────────────────────────────────────────

def test_forgot_password_silent_for_unknown_email(client, db):
    r = client.post("/auth/forgot-password", data={"email": "missing@test.com"})
    # Same flash whether or not account exists — avoid enumeration
    assert r.status_code in (302, 303)


def test_forgot_password_generates_token(client, db):
    alice = make_user(db)
    client.post("/auth/forgot-password", data={"email": "alice@test.com"})
    db.session.refresh(alice)
    assert alice.reset_token is not None
    assert alice.reset_token_expires is not None


def test_reset_password_with_valid_token(client, db):
    alice = make_user(db)
    client.post("/auth/forgot-password", data={"email": "alice@test.com"})
    db.session.refresh(alice)
    token = alice.reset_token

    r = client.post(f"/auth/reset-password/{token}", data={
        "new_password": "newsecret456", "confirm_new_password": "newsecret456",
    }, follow_redirects=False)
    assert r.status_code in (302, 303)

    db.session.refresh(alice)
    assert alice.reset_token is None  # single-use token cleared
    assert alice.check_password("newsecret456")
    assert not alice.check_password("password123")


def test_reset_password_expired_token_rejected(client, db):
    alice = make_user(db)
    alice.reset_token = "expired-token-123"
    alice.reset_token_expires = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2)
    db.session.commit()

    r = client.post("/auth/reset-password/expired-token-123", data={
        "new_password": "newsecret456", "confirm_new_password": "newsecret456",
    }, follow_redirects=False)
    # Redirects back to forgot-password with error flash
    assert r.status_code in (302, 303)
    db.session.refresh(alice)
    assert alice.check_password("password123")  # password unchanged


def test_reset_password_unknown_token_rejected(client, db):
    r = client.get("/auth/reset-password/nonexistent-token")
    assert r.status_code in (302, 303)


# ── Role gates ─────────────────────────────────────────────────

def test_admin_only_page_forbidden_for_regular_user(client, db):
    make_user(db)
    login(client, "alice")
    r = client.get("/admin/users")
    assert r.status_code == 403


def test_admin_only_page_ok_for_admin(client, db):
    make_user(db, is_admin=True)
    login(client, "alice")
    r = client.get("/admin/users")
    assert r.status_code == 200


def test_mod_can_access_events_admin(client, db):
    make_user(db, is_moderator=True)
    login(client, "alice")
    r = client.get("/admin/events")
    assert r.status_code == 200


def test_mod_cannot_access_users_admin(client, db):
    make_user(db, is_moderator=True)
    login(client, "alice")
    r = client.get("/admin/users")
    assert r.status_code == 403


def test_toggle_mod_requires_admin(client, db):
    make_user(db, is_moderator=True)  # a mod, not an admin
    target = make_user(db, email="target@test.com", username="target")
    login(client, "alice")
    r = client.post(f"/admin/users/{target.id}/toggle-mod")
    assert r.status_code == 403


# ── Event RSVPs ───────────────────────────────────────────────

def _make_event(db, *, allow_rsvp=True, is_public=True, slug="test-event"):
    ev = Event(
        title="Test Event", slug=slug,
        start_date=datetime.now(timezone.utc).date() + timedelta(days=7),
        status="published", is_public=is_public, allow_rsvp=allow_rsvp,
        category="general",
    )
    db.session.add(ev)
    db.session.commit()
    return ev


def test_join_requires_login(client, db):
    ev = _make_event(db)
    r = client.post(f"/events/{ev.slug}/join", follow_redirects=False)
    assert r.status_code in (302, 303, 401)  # redirected to login


def test_join_creates_rsvp(client, db):
    alice = make_user(db)
    ev = _make_event(db)
    login(client, "alice")
    r = client.post(f"/events/{ev.slug}/join", follow_redirects=False)
    assert r.status_code in (302, 303)
    rsvp = EventRSVP.query.filter_by(event_id=ev.id, user_id=alice.id).first()
    assert rsvp is not None


def test_double_join_does_not_create_two_rsvps(client, db):
    alice = make_user(db)
    ev = _make_event(db)
    login(client, "alice")
    client.post(f"/events/{ev.slug}/join")
    client.post(f"/events/{ev.slug}/join")
    count = EventRSVP.query.filter_by(event_id=ev.id, user_id=alice.id).count()
    assert count == 1


def test_join_blocked_when_allow_rsvp_false(client, db):
    make_user(db)
    ev = _make_event(db, allow_rsvp=False, slug="no-rsvp-event")
    login(client, "alice")
    client.post(f"/events/{ev.slug}/join")
    assert EventRSVP.query.filter_by(event_id=ev.id).count() == 0


# ── Thread posts ──────────────────────────────────────────────

def test_post_requires_rsvp(client, db):
    make_user(db)
    ev = _make_event(db)
    login(client, "alice")
    # Post without joining first
    r = client.post(f"/events/{ev.slug}/posts", data={"body": "hi"}, follow_redirects=False)
    # Flashes and redirects without creating a post
    assert EventPost.query.count() == 0


def test_post_created_after_join(client, db):
    make_user(db)
    ev = _make_event(db)
    login(client, "alice")
    client.post(f"/events/{ev.slug}/join")
    client.post(f"/events/{ev.slug}/posts", data={"body": "hello thread"})
    assert EventPost.query.filter_by(event_id=ev.id).count() == 1


def test_author_can_delete_own_post(client, db):
    alice = make_user(db)
    ev = _make_event(db)
    login(client, "alice")
    client.post(f"/events/{ev.slug}/join")
    client.post(f"/events/{ev.slug}/posts", data={"body": "mine"})
    post = EventPost.query.filter_by(user_id=alice.id).first()

    client.post(f"/events/{ev.slug}/posts/{post.id}/delete")
    assert db.session.get(EventPost, post.id) is None


def test_non_author_non_mod_cannot_delete(client, db):
    alice = make_user(db)
    bob = make_user(db, email="bob@test.com", username="bob")
    ev = _make_event(db)
    # Alice writes a post
    login(client, "alice")
    client.post(f"/events/{ev.slug}/join")
    client.post(f"/events/{ev.slug}/posts", data={"body": "alice's"})
    post = EventPost.query.filter_by(user_id=alice.id).first()
    # Bob logs in and tries to delete
    client.get("/auth/logout")  # may fail since logout is POST-only
    client.post("/auth/logout")
    login(client, "bob")
    r = client.post(f"/events/{ev.slug}/posts/{post.id}/delete")
    assert r.status_code == 403
    assert db.session.get(EventPost, post.id) is not None


def test_mod_can_delete_any_post(client, db):
    alice = make_user(db)
    mod = make_user(db, email="mod@test.com", username="modder", is_moderator=True)
    ev = _make_event(db)
    # Alice posts
    login(client, "alice")
    client.post(f"/events/{ev.slug}/join")
    client.post(f"/events/{ev.slug}/posts", data={"body": "spam maybe"})
    post = EventPost.query.filter_by(user_id=alice.id).first()
    # Logout alice, login mod
    client.post("/auth/logout")
    login(client, "modder")
    client.post(f"/events/{ev.slug}/posts/{post.id}/delete")
    assert db.session.get(EventPost, post.id) is None


# ── Account lock + session revocation ─────────────────────────

def test_locked_user_cannot_log_in(client, db):
    make_user(db, is_locked=True)
    r = login(client, "alice")
    assert r.status_code == 403


def test_admin_can_lock_user(client, db):
    admin = make_user(db, email="admin@test.com", username="admin", is_admin=True)
    target = make_user(db)
    login(client, "admin")
    r = client.post(f"/admin/users/{target.id}/toggle-lock", follow_redirects=False)
    assert r.status_code in (302, 303)
    db.session.refresh(target)
    assert target.is_locked is True
    # Locking a user must also bump their session_version so existing cookies die.
    assert (target.session_version or 0) >= 1


def test_admin_cannot_lock_self(client, db):
    admin = make_user(db, email="admin@test.com", username="admin", is_admin=True)
    login(client, "admin")
    client.post(f"/admin/users/{admin.id}/toggle-lock", follow_redirects=False)
    db.session.refresh(admin)
    assert admin.is_locked is False


def test_non_admin_cannot_toggle_lock(client, db):
    make_user(db)  # alice, not admin
    target = make_user(db, email="target@test.com", username="target")
    login(client, "alice")
    r = client.post(f"/admin/users/{target.id}/toggle-lock")
    assert r.status_code == 403


def test_revoke_other_sessions_bumps_version(client, db):
    alice = make_user(db)
    login(client, "alice")
    before = (alice.session_version or 0)
    r = client.post("/auth/account/sessions/revoke-all", follow_redirects=False)
    assert r.status_code in (302, 303)
    db.session.refresh(alice)
    assert (alice.session_version or 0) == before + 1


def test_revoke_keeps_current_session_valid(client, db):
    """The caller of revoke-all should stay signed in on THIS device."""
    make_user(db)
    login(client, "alice")
    client.post("/auth/account/sessions/revoke-all")
    # Still authenticated on this client
    r = client.get("/auth/account", follow_redirects=False)
    assert r.status_code == 200


def test_load_user_rejects_stale_session_version(app, db):
    """A cookie carrying an old session_version should refuse to authenticate."""
    alice = make_user(db)
    loader = app.login_manager._user_callback
    # current version is 0; a cookie that encoded version 99 is stale
    assert loader(f"{alice.id}:99") is None
    assert loader(f"{alice.id}:0") is not None  # current version works


def test_load_user_rejects_locked_account(app, db):
    """Locked users should not authenticate from any existing cookie."""
    alice = make_user(db, is_locked=True)
    loader = app.login_manager._user_callback
    assert loader(f"{alice.id}:0") is None


# ── Opening posts (no RSVP required) ──────────────────────────

def test_logged_in_user_can_post_on_opening(client, db):
    make_user(db)
    op = Opening(title="Room A", slug="room-a", status="published")
    db.session.add(op)
    db.session.commit()
    login(client, "alice")
    client.post(f"/openings/{op.slug}/posts", data={"body": "is parking included?"})
    assert OpeningPost.query.filter_by(opening_id=op.id).count() == 1
