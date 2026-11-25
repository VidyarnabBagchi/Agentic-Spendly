import os
import sqlite3

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from database.db import (
    create_user,
    get_db,
    get_user_by_email,
    init_db,
    seed_db,
    verify_user,
)

app = Flask(__name__)
# Dev fallback only — set SECRET_KEY in the environment for real deployments.
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

with app.app_context():
    init_db()
    seed_db()


DUPLICATE_EMAIL_MSG = "An account with that email already exists."
INVALID_LOGIN_MSG = "Invalid email or password."


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _validate_registration(name, email, password):
    """Return the first validation error message, or None if valid.

    Expects name/email already stripped and email lowercased.
    """
    if not name or not email or not password.strip():
        return "All fields are required."
    _, at, domain = email.partition("@")
    if not at or "." not in domain:
        return "Please enter a valid email address."
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if get_user_by_email(email) is not None:
        return DUPLICATE_EMAIL_MSG
    return None


def _render_register_error(error, name, email):
    """Re-render the register form with an error (password never echoed)."""
    return render_template(
        "register.html", error=error, name=name, email=email
    ), 400


def _render_login_error(email):
    """Re-render the login form with a generic error (password never echoed)."""
    return render_template(
        "login.html", error=INVALID_LOGIN_MSG, email=email
    ), 401


def _start_session(user):
    """Start a fresh session for user, storing only id and name."""
    session.clear()  # drop any pre-login session data (anti-fixation)
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]


# ------------------------------------------------------------------ #
# Routes                                                            #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    # User-input errors re-render the form (400) instead of abort(),
    # so the user gets their entered values back.
    error = _validate_registration(name, email, password)
    if error:
        return _render_register_error(error, name, email)

    try:
        create_user(name, email, password)
    except sqlite3.IntegrityError:
        return _render_register_error(DUPLICATE_EMAIL_MSG, name, email)

    flash("Account created. Please sign in.", "success")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    # Bad credentials re-render the form (401) instead of abort(), so the
    # user keeps their email. Unknown email and wrong password share one
    # message so the form never reveals which emails are registered.
    user = verify_user(email, password)
    if user is None:
        return _render_login_error(email)

    _start_session(user)
    return redirect(url_for("landing"))


@app.route("/logout")
def logout():
    session.clear()
    # Flash after clear(): flashed messages are stored in the session.
    flash("You have been signed out.", "success")
    return redirect(url_for("landing"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
