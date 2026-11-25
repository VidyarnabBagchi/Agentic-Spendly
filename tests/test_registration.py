import os

import pytest
from werkzeug.security import check_password_hash

import database.db as db

VALID = {
    "name": "Test User",
    "email": "test@example.com",
    "password": "password123",
}
DUPLICATE_MSG = "An account with that email already exists."


def post_register(client, **overrides):
    return client.post("/register", data={**VALID, **overrides})


def test_get_register_renders_form(client):
    resp = client.get("/register")
    assert resp.status_code == 200
    assert b'name="password"' in resp.data


def test_valid_registration_creates_one_user(client, users_with_email):
    resp = post_register(client)

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")
    rows = users_with_email(VALID["email"])
    assert len(rows) == 1
    assert rows[0]["name"] == VALID["name"]
    assert rows[0]["password_hash"] != VALID["password"]
    assert check_password_hash(rows[0]["password_hash"], VALID["password"])


def test_success_redirects_to_login_with_flash(client):
    resp = client.post("/register", data=VALID, follow_redirects=True)

    assert resp.status_code == 200
    assert resp.request.path == "/login"
    assert b"Account created. Please sign in." in resp.data
    assert b"auth-success" in resp.data


def test_email_is_normalised(client, users_with_email):
    post_register(client, email="  Test@Example.COM  ")

    assert len(users_with_email("test@example.com")) == 1
    assert users_with_email("  Test@Example.COM  ") == []


def test_duplicate_email_any_case_rejected(client, users_with_email):
    post_register(client)
    resp = post_register(client, email="TEST@example.com")

    assert resp.status_code == 400
    assert DUPLICATE_MSG.encode() in resp.data
    assert len(users_with_email(VALID["email"])) == 1


def test_duplicate_integrity_error_path(client, monkeypatch, users_with_email):
    """Simulate a race: pre-check misses, UNIQUE constraint catches it."""
    import app as app_module

    monkeypatch.setattr(app_module, "get_user_by_email", lambda email: None)
    post_register(client)
    resp = post_register(client)

    assert resp.status_code == 400
    assert DUPLICATE_MSG.encode() in resp.data
    assert len(users_with_email(VALID["email"])) == 1


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"name": ""}, "All fields are required."),
        ({"name": "   "}, "All fields are required."),
        ({"email": "   "}, "All fields are required."),
        ({"password": ""}, "All fields are required."),
        ({"password": "        "}, "All fields are required."),
        ({"email": "bad-email"}, "Please enter a valid email address."),
        ({"email": "a@b"}, "Please enter a valid email address."),
        ({"password": "short12"}, "Password must be at least 8 characters."),
    ],
)
def test_validation_errors(client, users_with_email, overrides, message):
    resp = post_register(client, **overrides)

    assert resp.status_code == 400
    assert message.encode() in resp.data
    email = overrides.get("email", VALID["email"]).strip().lower()
    assert users_with_email(email) == []


def test_validation_shows_first_error_only(client):
    resp = post_register(client, name="", email="bad-email")

    assert b"All fields are required." in resp.data
    assert b"Please enter a valid email address." not in resp.data


def test_error_preserves_name_email_not_password(client):
    resp = post_register(client, password="secret7")

    assert resp.status_code == 400
    assert b'value="Test User"' in resp.data
    assert b'value="test@example.com"' in resp.data
    assert b"secret7" not in resp.data


def test_form_action_uses_url_for(client):
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "templates", "register.html"
    )
    with open(path, encoding="utf-8") as f:
        source = f.read()

    assert "url_for('register')" in source
    assert 'action="/register"' not in source
    assert b'action="/register"' in client.get("/register").data


def test_uses_temp_database(app, tmp_path):
    assert db.DB_PATH.startswith(str(tmp_path))
    assert not db.DB_PATH.endswith("expense_tracker.db")
