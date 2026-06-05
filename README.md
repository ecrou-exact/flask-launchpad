# Flask Launchpad

A production-ready Flask application template with a full authentication system, role-based access control, per-user settings, a structured logging layer, and a Vue 3 frontend design system.

---

## Getting started

**Prerequisites:** Python 3.10+, pip

```bash
# First-time setup — creates the venv, installs deps, and seeds the database
./launch.sh --setup

# Start the development server
./launch.sh --start
```

The dev server runs at `http://127.0.0.1:7009`.

Default admin account: `admin@admin.admin` / `admin`

---

## Available commands

| Command | What it does |
|---|---|
| `./launch.sh --setup` | First-run: virtualenv, dependencies, initial database |
| `./launch.sh --start` | Start the development server |
| `./launch.sh --test` | Run the full pytest suite |
| `./launch.sh --test -v tests/account/` | Run tests for a specific feature |
| `./launch.sh --migrate "description"` | Generate a new Alembic migration |
| `./launch.sh --upgrade` | Apply pending database migrations |
| `./launch.sh --reload-db` | Drop and recreate the database from scratch |

---

## Features

### Authentication

Full session-based authentication built on Flask-Login. Users can register, log in, and manage their own profile — avatar upload, bio, social links, job title, company, location. Password hashing uses bcrypt. Sessions are server-side via Flask-Session. Force-logout is available to administrators: flipping a flag on a user invalidates their active session on the next request.

### Role-based access control

Every user belongs to exactly one role. Roles carry two special flags — `admin` (full unrestricted access) and `read_only` (restricted to safe operations) — plus an arbitrary set of granular permission keys. The permission system is consistent across HTML routes (`require_permission(key)`) and the REST API (`api_require_permission(key)`), with the same semantics in Vue templates via the global `hasPerm()` helper.

### Per-user configuration

Each user has an independent preferences record: theme, navigation layout, toast position, toast style, and toast duration. Changes apply immediately via the API — no page reload. Seven themes are available (warm, dark, ocean, forest, midnight, slate, system). Four navigation modes are supported: sidebar, topbar, rail, and hidden.

### Admin panel

Administrators have a dedicated area for user management — view, edit, verify, force-disconnect, soft-delete, and bulk operations on users. A log viewer shows the full application activity feed, filterable by category, level, actor, and date. Role management covers creating custom roles with specific permission keys, colors, and icons.

### Structured logging

Every mutating action in the application produces a structured log entry via `log_action()`. Entries carry a machine-readable action key, a category, a severity level, the actor, IP address, user-agent, the target object type and ID, and a typed metadata dict. Logs are never broken by application errors — the helper is safe to call from anywhere without a try/except.

### REST API

A Flask-RESTX API is available at `/api/` with interactive Swagger documentation. All endpoints require an `X-API-KEY` header for external access. Internal frontend calls authenticate via the existing session. The API mirrors every HTML feature: user management, configuration, logs.

### Design system

The frontend is built on a CSS custom-property design system ("Warm Studio") with full dark-mode support. All spacing, color, typography, shadow, and animation values are exposed as tokens — any component that references only tokens is automatically theme-compatible. Reusable Vue 3 components include a full-featured data table (sort, filter, paginate, bulk select), a loading bar, pagination, role badge, user avatar, modal confirm, and a password strength indicator.

---

## Project structure

```
app/
  features/          Flask blueprints, one folder per feature
  api/               Flask-RESTX resources + verification modules
  core/
    db_class/        SQLAlchemy models
    utils/           Decorators, logger, utilities
  templates/         Jinja2 templates extending base.html
  static/
    css/             One file per feature, core design system
    js/
      constants.js   TOAST, CSRF_TOKEN, apiFetch()
      toaster.js     create_message()
      components/    Vue 3 components

tests/               Pytest suite mirroring the features/ structure
```

---

## Developer reference

Full coding conventions, architecture patterns, logging guide, component documentation, and the new-feature checklist are available in the in-app documentation at `/docs` (requires login).
