# Spec: Registration

## Overview
Make the existing `/register` page actually create accounts. `GET /register`
already renders the form, but submitting it hits a route that only accepts GET.
This step adds the POST handler: validate the submitted name, email and
password, reject duplicate emails, store the user with a werkzeug-hashed
password, and send the new user to the login page with a success message.
Registration is the first step of the auth flow. Login and logout (Step 3)
and the profile page (Step 4) need real user rows to exist, so this step
comes before them. It does **not** log the user in. Sessions and login belong
to Step 3.

## Depends on
- **Step 1: Database setup.** Needs the `users` table, `get_db()` and
  `init_db()` in `database/db.py` (all present).

## Routes
- `GET /register`: render the registration form (already exists, unchanged
  behaviour). Public.
- `POST /register`: validate the form, create the user, then redirect to
  `GET /login` with a flash success message. On validation failure, re-render
  `register.html` with an error and the previously entered name and email
  (never the password). Public.

Both are served by the existing `register()` view, changed to
`methods=["GET", "POST"]`. No other routes are added or changed.

## Database changes
No database changes. The existing `users` table already has everything
needed (`name`, `email UNIQUE`, `password_hash`, `created_at` default).

New helper functions in `database/db.py` (no schema change):
- `get_user_by_email(email)`: returns the matching `sqlite3.Row` or `None`.
- `create_user(name, email, password)`: hashes the password with
  `generate_password_hash`, inserts the row, commits, and returns the new user
  id. Closes the connection in a `finally` block.

## Templates
- **Create:** none
- **Modify:**
  - `templates/register.html`:
    - Change `action="/register"` to `action="{{ url_for('register') }}"`
      (this fixes a hardcoded URL that breaks the CLAUDE.md rules).
    - Re-populate `name` and `email` inputs from the submitted values on error
      (`value="{{ name or '' }}"`).
    - Add `minlength="8"` to the password input so it matches the server rule.
  - `templates/login.html`: render flashed messages (success category) above
    the form, using a new `.auth-success` style.

## Files to change
- `app.py`: set `app.secret_key` (from the `SECRET_KEY` env var with a dev
  fallback; this is needed for `flash`), add `POST` to `register()`, and
  import `request`, `redirect`, `url_for` and `flash`, plus the new db helpers.
- `database/db.py`: add `get_user_by_email()` and `create_user()`.
- `templates/register.html`: see Templates.
- `templates/login.html`: see Templates.
- `static/css/style.css`: add `.auth-success` next to the existing
  `.auth-error`, using `--accent` / `--accent-light` variables.
- `CLAUDE.md`: mark `POST /register` as implemented in the routes table.

## Files to create
- `tests/conftest.py`: a pytest fixture that points `database.db.DB_PATH`
  at a `tmp_path` SQLite file, runs `init_db()`, and yields a Flask test
  client, so tests never touch `expense_tracker.db`.
- `tests/test_registration.py`: tests covering the Definition of done.

## New dependencies
No new dependencies. Flask, werkzeug, pytest and pytest-flask are already in
`requirements.txt`.

## Rules for implementation
- No SQLAlchemy or ORMs. Use raw `sqlite3` via `get_db()` only.
- Parameterised queries only (`?` placeholders). Never use f-strings or
  `%` formatting in SQL.
- Passwords hashed with werkzeug `generate_password_hash`. Never store or
  log plaintext.
- Use CSS variables. Never hardcode hex values in new CSS.
- All templates extend `base.html`.
- All DB access lives in `database/db.py`. The route calls helpers only.
- Use `url_for()` for every internal link and redirect.
- Validation, in this order, with one error shown at a time:
  1. All three fields present after `.strip()`. Error: "All fields are required."
  2. Email contains `@` and a `.` after it. Error: "Please enter a valid email address."
  3. Password is at least 8 characters. Error: "Password must be at least 8 characters."
  4. Email not already registered. Error: "An account with that email already exists."
- Normalise email to `.strip().lower()` before the duplicate check and insert.
- Validation failures re-render the form with HTTP 400. Do not use `abort()`
  for user input errors, because the user needs the form back.
- Also catch `sqlite3.IntegrityError` on insert (a race on the UNIQUE email)
  and show the duplicate-email error.
- Do not log the user in or touch `session` (Step 3).
- Do not implement any other stub route.

## Definition of done
- [ ] `GET /register` still renders the form with status 200.
- [ ] Submitting valid name, email and an 8+ char password creates exactly
      one row in `users`. Its `password_hash` is not the plaintext password
      and passes `check_password_hash`.
- [ ] After a successful submit the browser lands on `/login` and sees
      "Account created. Please sign in." styled as a success message.
- [ ] Email is stored lowercase and trimmed (` Test@Example.COM ` is saved as
      `test@example.com`).
- [ ] Submitting an email that already exists (in any letter case) shows
      "An account with that email already exists." and creates no new row.
- [ ] A blank field, invalid email, or password shorter than 8 chars each
      shows the matching error, returns 400, and creates no row.
- [ ] On any error, the name and email fields keep the entered values and the
      password field is empty.
- [ ] The register form's `action` is generated by `url_for`. No hardcoded
      `/register` remains in the template.
- [ ] `pytest` passes, and the tests use a temporary database, not
      `expense_tracker.db`.
- [ ] The app still starts with `python app.py` on port 5001.
