import pytest

import database.db as db  # importing db.py has no side effects


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Flask app wired to a throwaway SQLite file.

    app.py runs init_db()/seed_db() on import, so DB_PATH must be patched
    *before* the import — never import app at module level in tests.
    """
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    from app import app as flask_app

    db.init_db()
    flask_app.config.update(TESTING=True)
    yield flask_app


@pytest.fixture
def users_with_email(app):
    """Return a function that fetches all users rows for a given email."""
    def _fetch(email):
        conn = db.get_db()
        try:
            return conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchall()
        finally:
            conn.close()
    return _fetch
