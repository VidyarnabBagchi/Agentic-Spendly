# Spec: Login and Logout

## Overview
This step adds session-based authentication so that registered users can sign in with their email and password and sign out again. `POST /login` checks the submitted credentials against the `users` table using werkzeug's `check_password_hash`. If they match, it stores the user's id and name in Flask's signed `session` cookie. The `/logout` stub becomes a real route that clears the session. The navbar in `base.html` also changes based on login state. Every later step (profile, add/edit/delete expenses) needs a known current user, so this is where Spendly gets its idea of "who is logged in".

## Depends on
- **Step 1 — Database setup** (merged): `users` table, `get_db()`, seeded demo user `demo@spendly.com` / `demo123`.
- **Step 2 — Registration** (on branch `feature/registration-01`, **not yet merged into `main`**). Step 3 needs these pieces from it:
  - `app.secret_key` (needed for `session` and `flash`)
  - `get_user_by_email(email)` in `database/db.py`
  - the `flash("Account created. Please sign in.", "success")` redirect to `/login`, and the flash rendering in `login.html`
  - `tests/conftest.py` fixtures (temporary DB and test client)

  Merge Step 2 into `main`, then merge or rebase it into this branch, **before** implementing. Otherwise you would have to re-implement these pieces here, and they would conflict with Step 2.

## Routes
- `GET /login`: renders the sign-in form. If someone is already logged in, it redirects to `landing` instead. Access: public.
- `POST /login`: validates the credentials. On success it sets the session and redirects to `landing`. On failure it re-renders `login.html` with the generic error "Invalid email or password." and status 401, keeping the entered email filled in. Access: public.
- `GET /logout`: clears the session, flashes "You have been signed out.", and redirects to `landing`. Replaces the Step 3 stub. Access: logged-in. If nobody is logged in, it still redirects without error.

`/login` changes from `GET` only to `methods=["GET", "POST"]`. `/logout` keeps its URL and endpoint name.

## Database changes
No database changes. The existing `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) already has everything needed.

New helper in `database/db.py`:
- `verify_user(email, password)`: looks up the user with `get_user_by_email(email)` and checks the password with `werkzeug.security.check_password_hash`. Returns the user row if the password matches, otherwise `None`. All credential checking stays in the DB layer, not in the route.

## Templates
- **Create:** none
- **Modify:**
  - `templates/login.html`:
    - change `action="/login"` to `action="{{ url_for('login') }}"`
    - pre-fill the email input with `value="{{ email or '' }}"` after a failed attempt
    - never echo the password back
    - show flashed messages (for example "Account created…" from Step 2, if not already present)
  - `templates/base.html`:
    - navbar: when `session.user_id` is set, show "Hi, {{ session.user_name }}" and a **Sign out** link (`url_for('logout')`); otherwise show the current Sign in / Get started links
    - render flashed messages so the logout message appears on the landing page
    - change the hardcoded footer links `/terms` and `/privacy` to `url_for('terms')` and `url_for('privacy')`

## Files to change
- `app.py`:
  - import `session`, plus `redirect`, `url_for`, `flash`, `request` if not already imported from Step 2
  - import `verify_user`
  - implement `login` (GET and POST) and `logout`
- `database/db.py`: add `verify_user()` and import `check_password_hash`
- `templates/login.html`: see Templates
- `templates/base.html`: see Templates
- `static/css/style.css`: navbar user greeting / sign-out link styles and flash message styles, using the existing CSS variables
- `CLAUDE.md`: mark `GET /logout` as Implemented in the routes table, and note `POST /login`

## Files to create
- `tests/test_login_logout.py`: pytest tests covering the Definition of done (uses the Step 2 `conftest.py` fixtures)

## New dependencies
No new dependencies. Uses Flask's built-in `session` and `werkzeug.security`, which are already in `requirements.txt`.

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only (`?` placeholders), never f-strings in SQL.
- Passwords hashed with werkzeug: verify with `check_password_hash` and never compare plaintext.
- Use CSS variables: never hardcode hex values (use `--accent`, `--danger`, `--ink-muted`, etc.).
- All templates extend `base.html`.
- DB access lives in `database/db.py` only. The `login` route calls `verify_user()` and never opens a connection itself.
- Normalise the email the same way registration does: `.strip().lower()`.
- Use one generic error message for an unknown email and for a wrong password, so the app never reveals which emails are registered.
- Store only `user_id` and `user_name` in `session`, never the password hash or the full row.
- Call `session.clear()` before setting the new keys at login, to prevent session fixation.
- `logout` uses `session.clear()` and then redirects. It must not render a raw string.
- Use `url_for()` for every internal link and redirect. Do not hardcode URLs.
- Do not implement `/profile` or any expense routes. They belong to later steps.
- Keep the app on port 5001.

## Definition of done
- [ ] `GET /login` renders the sign-in form with status 200.
- [ ] Signing in as `demo@spendly.com` / `demo123` redirects to `/`, and the navbar shows "Hi, Demo User" and a **Sign out** link.
- [ ] Email is case- and whitespace-insensitive: ` Demo@Spendly.com ` / `demo123` signs in successfully.
- [ ] A wrong password re-renders the form with status 401 and "Invalid email or password.", with the email still filled in and the password field empty.
- [ ] An unregistered email shows the exact same error and status as a wrong password.
- [ ] Visiting `/login` while logged in redirects to `/`.
- [ ] Clicking **Sign out** clears the session, redirects to `/`, shows "You have been signed out.", and the navbar returns to Sign in / Get started.
- [ ] Visiting `/logout` while logged out redirects to `/` without error.
- [ ] After registering a new account (Step 2), the "Account created. Please sign in." flash appears on `/login`, and the new credentials sign in successfully.
- [ ] The session cookie contains no password or hash, only `user_id` and `user_name`.
- [ ] `login.html` and `base.html` contain no hardcoded internal URLs.
- [ ] `pytest` passes, including `tests/test_login_logout.py`.
- [ ] `python app.py` starts on port 5001 without errors.
