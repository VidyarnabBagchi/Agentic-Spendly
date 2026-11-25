from pathlib import Path

import pytest

import database.db as db

NAME = "Demo User"
EMAIL = "demo@spendly.com"
PASSWORD = "demo123"
INVALID_MSG = b"Invalid email or password."
TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


@pytest.fixture
def user(app):
    """Create the login user; each test starts with an empty database."""
    return db.create_user(NAME, EMAIL, PASSWORD)


def post_login(client, follow_redirects=False, **overrides):
    data = {"email": EMAIL, "password": PASSWORD, **overrides}
    return client.post("/login", data=data, follow_redirects=follow_redirects)


def test_get_login_renders_form(client):
    resp = client.get("/login")

    assert resp.status_code == 200
    assert b'name="password"' in resp.data


def test_valid_login_redirects_to_landing(client, user):
    resp = post_login(client)

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_navbar_shows_greeting_after_login(client, user):
    resp = post_login(client, follow_redirects=True)

    assert resp.request.path == "/"
    assert b"Hi, Demo User" in resp.data
    assert b"Sign out" in resp.data


def test_email_is_case_and_whitespace_insensitive(client, user):
    resp = post_login(client, email="  Demo@Spendly.COM  ")

    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess["user_id"] == user


def test_wrong_password_returns_401_with_email_prefilled(client, user):
    resp = post_login(client, password="wrong-password")

    assert resp.status_code == 401
    assert INVALID_MSG in resp.data
    assert b'value="demo@spendly.com"' in resp.data
    assert b"wrong-password" not in resp.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_unknown_email_same_error_as_wrong_password(client, user):
    wrong_pw = post_login(client, password="wrong-password")
    unknown = post_login(client, email="nobody@spendly.com")

    assert unknown.status_code == wrong_pw.status_code == 401
    assert INVALID_MSG in unknown.data


def test_empty_fields_rejected(client, user):
    resp = post_login(client, email="", password="")

    assert resp.status_code == 401
    assert INVALID_MSG in resp.data


def test_login_page_redirects_when_logged_in(client, user):
    post_login(client)
    resp = client.get("/login")

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


@pytest.mark.parametrize("method", ["get", "post"])
def test_register_redirects_when_logged_in(client, user, users_with_email, method):
    post_login(client)
    data = {"name": "Other", "email": "other@example.com",
            "password": "longenough1"}
    resp = getattr(client, method)("/register", data=data)

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")
    assert users_with_email("other@example.com") == []


def test_logout_clears_session_and_flashes(client, user):
    post_login(client)
    resp = client.get("/logout", follow_redirects=True)

    assert resp.request.path == "/"
    assert b"You have been signed out." in resp.data
    assert b"Sign in" in resp.data
    assert b"Hi, " not in resp.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess
        assert "user_name" not in sess


def test_logout_when_logged_out_redirects(client):
    resp = client.get("/logout")

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_register_then_login_flow(client):
    resp = client.post(
        "/register",
        data={"name": "New Person", "email": "new@example.com",
              "password": "longenough1"},
        follow_redirects=True,
    )
    assert resp.request.path == "/login"
    assert resp.data.count(b"Account created. Please sign in.") == 1

    resp = post_login(client, email="new@example.com", password="longenough1",
                      follow_redirects=True)
    assert b"Hi, New Person" in resp.data


def test_session_contains_only_user_id_and_name(client, user):
    post_login(client)

    with client.session_transaction() as sess:
        assert set(sess.keys()) == {"user_id", "user_name"}
        assert sess["user_name"] == NAME
        assert PASSWORD not in map(str, sess.values())


@pytest.mark.parametrize("template", ["login.html", "base.html"])
def test_templates_have_no_hardcoded_internal_urls(template):
    source = (TEMPLATES / template).read_text()

    assert 'href="/' not in source
    assert 'action="/' not in source
