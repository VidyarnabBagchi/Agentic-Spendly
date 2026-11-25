import os
import sqlite3
from datetime import date

from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "expense_tracker.db")

CATEGORIES = (
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
)


def get_db():
    """Return a SQLite connection with dict-like rows and FK enforcement."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they do not exist. Safe to call repeatedly."""
    conn = get_db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                email         TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL
                            REFERENCES users(id) ON DELETE CASCADE,
                amount      REAL NOT NULL,
                category    TEXT NOT NULL,
                date        TEXT NOT NULL,
                description TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def get_user_by_email(email):
    """Return the users row matching email exactly, or None."""
    conn = get_db()
    try:
        return conn.execute(
            "SELECT id, name, email, password_hash, created_at "
            "FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    finally:
        conn.close()


def verify_user(email, password):
    """Return the users row if email/password match, otherwise None."""
    user = get_user_by_email(email)
    if user is not None and check_password_hash(user["password_hash"], password):
        return user
    return None


def create_user(name, email, password):
    """Hash password, insert a user, and return the new user id.

    Raises sqlite3.IntegrityError if the email is already registered.
    """
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _month_date(day):
    """Return a YYYY-MM-DD date in the current month, never in the future."""
    today = date.today()
    return today.replace(day=min(day, today.day)).isoformat()


def seed_db():
    """Insert a demo user and sample expenses, only if no users exist."""
    conn = get_db()
    try:
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
            return

        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        user_id = cur.lastrowid

        samples = [  # (day, amount, category, description)
            (1, 45.50, "Food", "Groceries"),
            (3, 12.00, "Transport", "Metro card top-up"),
            (5, 120.00, "Bills", "Electricity bill"),
            (8, 30.00, "Health", "Pharmacy"),
            (12, 18.99, "Entertainment", "Movie tickets"),
            (15, 75.25, "Shopping", "New shoes"),
            (20, 9.99, "Other", None),
            (25, 22.40, "Food", "Dinner out"),
        ]
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                (user_id, amount, category, _month_date(day), description)
                for day, amount, category, description in samples
            ],
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
