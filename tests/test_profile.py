import re
from pathlib import Path

import pytest

import database.db as db

NAME = "Demo User"
EMAIL = "demo@spendly.com"
PASSWORD = "demo123"
ROOT = Path(__file__).resolve().parent.parent
PROFILE_TEMPLATE = ROOT / "templates" / "profile.html"
PROFILE_CSS = ROOT / "static" / "css" / "profile.css"
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b")


@pytest.fixture
def user(app):
    """Create the login user; each test starts with an empty database."""
    return db.create_user(NAME, EMAIL, PASSWORD)


@pytest.fixture
def logged_in(client, user):
    resp = client.post("/login", data={"email": EMAIL, "password": PASSWORD})
    assert resp.status_code == 302
    return client


def get_profile(client):
    resp = client.get("/profile")
    assert resp.status_code == 200
    return resp.data.decode()


def test_profile_redirects_to_login_when_logged_out(client):
    resp = client.get("/profile")

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


def test_profile_renders_when_logged_in(logged_in):
    html = get_profile(logged_in)

    assert "coming in Step 4" not in html
    assert "css/profile.css" in html


def test_user_card_shows_name_email_and_member_since(logged_in):
    html = get_profile(logged_in)

    assert 'class="profile-avatar"' in html
    assert ">DU<" in html
    assert NAME in html
    assert EMAIL in html
    assert "Member since" in html


def test_summary_stats_present(logged_in):
    html = get_profile(logged_in)

    assert html.count('class="stat-card"') == 3
    for label in ("Total spent", "Transactions", "Top category"):
        assert label in html
    assert "₹334.13" in html
    assert ">Bills<" in html


def test_transaction_table_has_rows(logged_in):
    html = get_profile(logged_in)

    assert html.count('class="txn-row"') >= 3
    assert 'class="cat-badge cat-food"' in html
    assert "<td>—</td>" in html  # empty description placeholder


def test_category_breakdown_has_categories(logged_in):
    html = get_profile(logged_in)

    assert html.count('class="cat-row"') >= 3
    assert '<progress class="cat-bar cat-bills" value="120.0" max="334.13"' in html


def test_navbar_shows_logged_in_state_with_profile_link(logged_in):
    html = get_profile(logged_in)

    assert "Hi, Demo User" in html
    assert "Sign out" in html
    assert 'href="/profile"' in html


def test_navbar_hides_profile_link_when_logged_out(client):
    html = client.get("/").data.decode()

    assert 'href="/profile"' not in html


@pytest.mark.parametrize("path", [PROFILE_TEMPLATE, PROFILE_CSS])
def test_profile_files_have_no_hex_colors(path):
    assert not HEX_COLOR.search(path.read_text())


def test_profile_template_has_no_inline_styles_or_hardcoded_urls():
    source = PROFILE_TEMPLATE.read_text()

    assert "style=" not in source
    assert "<style" not in source
    assert 'href="/' not in source
