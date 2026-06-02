# Flask Launchpad — Codebase Guide

## What this project is

A Flask boilerplate/starter kit (named "P'tit Crolle" in the UI). It provides a ready-to-use foundation with user authentication, role management, a REST API, and three swappable UI layouts. The goal is to clone this and build a new app on top of it.

## Running the app

```bash
# First run — create the DB and seed an admin user
python app.py --init_db

# Start the dev server
python app.py

# Or use the launch script
./launch.sh
```

The `FLASKENV` environment variable selects the config (`development` / `testing`). It defaults to `development`.

Default dev server: `http://127.0.0.1:7009`  
Default admin credentials: `admin@admin.admin` / `admin`

## Project layout

```
app/
  __init__.py          # App factory (create_app), extension init, blueprint registration
  app.py               # Entry point: CLI args (--init_db / --recreate_db / --delete_db), 404 handler
  home.py              # home_blueprint — the "/" routes
  api.py               # api_blueprint — mounts flask-restx, registers API namespaces
  decorators.py        # @admin_required, @api_required

  db_class/
    db.py              # All SQLAlchemy models live here

  account/
    account.py         # account_blueprint — HTML/form routes (login, register, edit, logout)
    account_api.py     # REST API endpoints for account actions (flask-restx Resources)
    account_core.py    # DB logic: get_user, create_user_core, edit_user_core
    form.py            # WTForms form classes
    verification_api.py # Input validation for API payloads (no ORM calls from routes)

  utils/
    utils.py           # Shared helpers: form_to_dict, generate_api_key, redirect_to_home, etc.
    init_db.py         # Seed functions: create_admin(), create_user_test()

  templates/
    base.html / base_2.html / base_3.html   # Three layout variants
    home.html / home_2.html / home_3.html   # Landing pages, one per layout
    navbars/           # Sidebar partials (one per layout)
    macros/            # Reusable Jinja2 macros (_flashes.html, form_macros.html)
    account/           # Account-specific templates

  static/              # Bootstrap 5.3, Font Awesome 6.3, jQuery, Vue 3, Select2, dayjs, zxcvbn

migrations/            # Flask-Migrate / Alembic migration scripts
tests/
  conftest.py          # pytest fixtures (app, client, runner) — uses testing config + in-memory SQLite
  account/
    test_account.py
```

## Architecture patterns

### Module structure per feature: `feature/`

Each feature follows the same three-file split:

| File | Role |
|---|---|
| `feature.py` | Blueprint + route handlers. Only handles HTTP (parse form/JSON, flash, redirect, render_template). Never touches the DB directly. |
| `feature_core.py` | All DB logic. Functions receive plain dicts, return ORM objects or `(obj, message)` tuples. Named `*_core.py`. |
| `feature_api.py` | flask-restx `Resource` classes for the REST API version of the same actions. Calls `feature_core` and `verification_api`. |
| `verification_api.py` | Pure validation for API input — returns the cleaned dict or `{"message": "..."}` on error. No HTTP concern. |
| `form.py` | WTForms form classes for HTML routes. Named `*_form.py` or `form.py` inside the feature folder. |

### DB models — `app/db_class/db.py`

All models are defined in one file. The `db` SQLAlchemy instance comes from `app/__init__.py`.

Current models: `User`, `Role`, `AnonymousUser` (flask-login anonymous proxy).

`User` methods:
- `is_admin()` / `read_only()` — check role flags
- `username()` — returns `"first_name last_name"`
- `verify_password(password)` — bcrypt check
- `to_json()` — dict for API responses

### Three UI layouts

The session key `ui_version` (1/2/3) selects which base template to use. A context processor in `create_app()` injects `base_layout` into every template:

```python
# In any child template:
{% extends base_layout %}  # resolves to base.html, base_2.html, or base_3.html
```

Each base layout has its own sidebar partial (`navbars/sidebar.html`, `sidebar2.html`, `sidebar_top.html`) and CSS (`css/base_1/`, etc.). The home routes (`/`, `/2`, `/3`) set the session version on load.

`redirect_to_home()` in `utils.py` reads `session['ui_version']` to send the user back to the right layout after login/logout.

### REST API — `/api/`

Built with **flask-restx**. The swagger UI is at `/api/`.

Authentication: `X-API-KEY` header. The `@api_required` decorator (from `decorators.py`) validates it against `User.api_key`.

CSRF is exempted for the entire `api_blueprint`.

To add a new API namespace:
1. Create `feature/feature_api.py` with a `Namespace` and `Resource` classes.
2. Import the namespace in `api.py` and call `api.add_namespace(feature_ns, path="/feature")`.

### Forms pattern

In HTML routes, always convert a validated form to a plain dict before passing to `*_core`:

```python
form_dict = form_to_dict(form)  # strips submit + csrf_token fields
result, message = FeatureModel.do_something_core(form_dict)
```

### Decorators

- `@login_required` — flask-login, redirects to `account.login`
- `@admin_required` — works for both HTML routes (checks `current_user`) and API routes (checks `X-API-KEY`)
- `@api_required` — API key presence + validity check

## Config

Copy `config.py.default` to `config.py`. Selected by `FLASKENV` env var.

- `development`: SQLite (`ptitcrolle.sqlite`), debug on, server-side sessions stored in SQLAlchemy
- `testing`: separate SQLite (`ptitcrolle-test.sqlite`), CSRF disabled, used by pytest

## Testing

```bash
pytest
```

`conftest.py` creates a fresh DB per test session using `create_user_test()` which seeds three users:
- `admin@admin.admin` / `admin` — role_id 1 (Admin)
- `editor@editor.editor` / `editor` — role_id 2 (Editor)
- `read@read.read` / `read` — role_id 3 (Read Only)

Tests use the Flask test client (`client` fixture). API tests hit `/api/` endpoints with `content_type='application/json'`.

## Adding a new feature — checklist

1. Create `app/feature/` with `__init__.py` (empty), `feature.py` (blueprint), `feature_core.py`, `form.py`.
2. Add models to `app/db_class/db.py`.
3. Register the blueprint in `app/__init__.py`.
4. Add a migration: `flask db migrate -m "add feature" && flask db upgrade`.
5. Add templates under `app/templates/feature/`, extending `{{ base_layout }}`.
6. Optionally add `feature_api.py` + `verification_api.py` and register the namespace in `api.py`.
