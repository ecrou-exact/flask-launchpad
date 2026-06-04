# Flask Launchpad — Codebase Guide

## Non-negotiable rules

- **Commands** — everything via `./launch.sh`. Never call `python app.py` or `flask` directly.
- **Routes** — never touch the DB. Always: `form_to_dict()` → `*_core()` → flash/redirect.
- **Core** — always returns `(object, "message")`. Logs go in core, never in routes.
- **Access** — every route needs explicit decorators: `@login_required` / `@admin_required` / `@feature_required('key')`. No naked route.
- **Deletion** — never physically delete from a user action. Soft delete only. Hard delete from `/admin/<feature>/trash`.
- **URLs** — UUID in all public-facing links. Routes accept both via `get_by_id_or_uuid()`.
- **JS** — Composition API, ES modules, `[[...]]` delimiters, `TOAST.*` + `apiFetch()` from `constants.js`, never `console.log`. Toast: always `create_message()`, never `display_toast()` in templates.
- **CSS** — `var(--bg-body)` / `var(--text-main)`, never hardcode colors. One file per feature in `static/css/<feature>/`.
- **Tables** — always `<data-table>`. Never build a table from scratch.
- **Charts** — always Apache ECharts wrapped in `chart-<type>.js` component.
- **Security** — `bandit -r app/` + `safety check` before delivery. Never `{{ var | safe }}` on user data.
- **Tests** — every feature or route addition gets a test file. Always run `./launch.sh --test` before declaring done.
- **CSS / Architecture** — always reuse existing CSS classes and components before creating new ones. Check `static/css/` and `static/js/components/` first.
- **File structure** — create `app/features/<feature>/` + `app/api/<feature>_api.py` + `tests/<feature>/` for each new feature. If the feature belongs to an existing domain (e.g. adding a route to `account`), add to the existing files — never create a parallel folder.
- **API** — every new HTML route that reads/writes data must have a matching API endpoint. Update `app/api/<feature>_api.py` and register the namespace in `api.py`.
- **Nav + search + permissions** — all driven from two files only. Never modify `_nav.html` or `_search_sections.html` for new features.
- **Every new feature** must cover all 9 blocks: structure · model · access · CRUD · logs · jobs · tests · docs · security.

---

## Running the app

| Command | Description |
|---|---|
| `./launch.sh --setup` | First run: venv, deps, config, init DB |
| `./launch.sh --start` | Start dev server |
| `./launch.sh --test` | Run pytest |
| `./launch.sh --test -v tests/account/` | Targeted tests |
| `./launch.sh --migrate "message"` | Create Alembic migration |
| `./launch.sh --upgrade` | Apply pending migrations |
| `./launch.sh --reload-db` | Drop + recreate DB |

Dev server: `http://127.0.0.1:7009` — Admin: `admin@admin.admin` / `admin`

---

## Project layout

```
app/
  __init__.py              # create_app(), extensions, blueprint registration

  api/
    api.py                 # api_blueprint — flask-restx, namespace registry
    account_api.py
    admin_api.py
    config_api.py
    log_api.py
    verification_api.py
    verification_config.py

  core/
    db_class/
      user.py              # User, Role, AnonymousUser
      log.py               # Log model
      config.py            # UserConfig model (per-user preferences)
      site_config.py       # SiteConfig model (global key-value config)
    utils/
      decorators.py        # @admin_required, @api_required, @login_required, @feature_required
      utils.py             # form_to_dict, generate_api_key, get_by_id_or_uuid
      logger.py            # log_action()
      init_db.py           # Seed functions

  features/
    home/home.py
    account/               # account.py, account_core.py, form.py
    admin/admin.py         # user management, log viewer
    config/                # config.py, config_core.py, form.py (site settings)

  templates/
    base.html
    home.html
    account/               # login.html, create.html, edit.html, profile.html
    admin/                 # users.html, user_detail.html, logs.html
    config/settings.html
    macros/                # _flashes.html, _nav.html, _footer.html, form_macros.html
    utils/                 # 403.html, 404.html, 500.html

  static/
    css/core.css, login.css
    js/
      theme.js, blur.js
      constants.js         # TOAST, CSRF_TOKEN, apiFetch()
      toaster.js           # create_message(), display_toast()
      components/
        loading-bar.js, pagination.js, data-table.js

tests/
  conftest.py
  account/test_account.py
```

---

## Models

### User (`app/core/db_class/user.py`)

| Field | Type | Notes |
|---|---|---|
| `id`, `email`, `password_hash`, `api_key` | identity | — |
| `first_name`, `last_name`, `username` | profile | `display_name()`, `initials()` |
| `role_id` | FK → Role | `is_admin()`, `read_only()` |
| `bio`, `avatar_filename`, `phone`, `job_title`, `company`, `location` | profile | — |
| `website`, `social_twitter`, `social_github`, `social_linkedin` | links | — |
| `is_verified`, `force_logout`, `session_version`, `last_seen_at` | status | `force_logout` triggers auto-disconnect |
| `created_at` | timestamp | — |

### Role (`app/core/db_class/user.py`)

`id`, `name`, `description`, `admin` (bool), `read_only` (bool)

### Log (`app/core/db_class/log.py`)

| Field | Values / Notes |
|---|---|
| `id`, `uuid` | — |
| `title` | Short human-readable summary |
| `action` | Machine key: `login`, `create`, `edit`, `delete`, `bulk_delete`, … |
| `category` | `user` · `system` · `security` · `admin` · `api` |
| `level` | `info` · `success` · `warning` · `error` |
| `description` | Optional long text |
| `object_type`, `object_id` | Target model + UUID/ID (never names) |
| `actor_id`, `ip_address`, `user_agent` | Auto-detected from request context |
| `is_public` | `False` = admin only / `True` = all authenticated users |
| `meta` | JSON dict — IDs only, never plain names |
| `created_at` | — |

### UserConfig (`app/core/db_class/config.py`)

Per-user preferences. Full standard fields (id, uuid, is_active, …) +  
`theme`, `nav_position`, `sidebar_collapsed`, `toast_position`, `toast_style`, `toast_duration`.  
Choices defined as module-level constants (`THEME_CHOICES`, `NAV_POSITION_CHOICES`, …).  
Injected into every template via `inject_user_config` context processor.

### SiteConfig (`app/core/db_class/site_config.py`)

Global key-value config. Helpers: `get_site_value(key)`, `get_site_bool(key)`, `set_site_value(key, value)`.  
Current keys: `allow_registration`, `allow_login`.  
Injected into every template via `inject_site_config`.

### Standard model fields (every new model)

```
id, uuid (auto), title, description, is_public (False),
created_at, updated_at, created_by,
is_active (True), deleted_at, deleted_by,
meta (JSON)
```

---

## Log system

```python
from app.core.utils.logger import log_action

log_action(
    title="User logged in",        # required — human summary
    action="login",                # required — machine key
    category="user",               # user | system | security | admin | api
    level="success",               # info | success | warning | error
    object_type="user",            # optional
    object_id=user.id,             # optional — coerced to str
    is_public=False,               # False = admin only
    meta={"role_id": user.role_id} # IDs only, never names
)
```

- Call from `*_core.py` only — never from routes or API resources.
- Actor and IP are auto-detected; `actor_id` param overrides.
- Never raises — logging failure cannot break the request.

### Standard actions

| action | category | is_public |
|---|---|---|
| `login` / `logout` | `user` | `False` |
| `create` / `edit` | feature name | `True` |
| `delete` / `restore` / `hard_delete` | feature name | `False` |
| `bulk_delete` / `bulk_edit` | feature name | `False` |

**Règle catégorie** : tout `log_action` dans un fichier `*_api.py` utilise obligatoirement `category="api"`, quelle que soit la sévérité ou le type d'action.

**Logging automatique** : seuls les appels avec `X-API-KEY` (appels externes) sont loggés automatiquement via `after_request` dans `api.py`. Les appels internes du frontend (session auth, sans clé) ne sont pas loggés ici. Le `meta` contient `method`, `path`, `status_code`, `request_body` (champs sensibles masqués) et `response`.

---

## Adding a new feature — quick reference

### The two files to edit

| File | What to add |
|---|---|
| `app/core/utils/permissions.py` | The permission key(s) for this feature |
| `app/core/utils/nav_registry.py` | The nav item(s) — nav + search auto-update |

Everything else (nav, sidebar, search bar, topbar) updates automatically. Never touch `_nav.html` or `_search_sections.html`.

### Route (Python)
```python
from app.core.utils.decorators import require_permission

@feature_blueprint.route('/')
@require_permission()                    # any authenticated user
@require_permission('feature.view')      # specific permission (or admin)
@require_permission('admin_only')        # admin only
def index(): ...
```

**Routes never touch the DB.** Always call a `*_core()` function:
```python
# ✓
from .feature_core import get_item_or_404
def detail(uid): item = get_item_or_404(uid) ...

# ✗
from ...core.db_class.user import User
def detail(uid): user = User.query.get_or_404(uid) ...
```

### Template (Vue buttons)
```javascript
// USER_PERMS and hasPerm() are global — no import needed
const can_edit   = hasPerm('feature.edit')
const can_delete = hasPerm('feature.delete')
```
```html
<data-table :can-edit="can_edit" :can-delete="can_delete" ...>
```

### Permission values in nav_registry.py
- `None` → all authenticated users
- `'key'` → users who have that permission (or admins)
- `'admin_only'` → admins only

---

## API routes reference

Swagger UI at `http://127.0.0.1:7009/api/`. Auth: `X-API-KEY` header.

### `/api/account` — User management

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/account/me` | api_required | Current user profile |
| PUT | `/api/account/me` | api_required | Edit own profile |
| POST | `/api/account/me/reload-api-key` | api_required | Regenerate own API key |
| GET | `/api/account/user/<uid>` | api_required | Get user by id |
| POST | `/api/account/add_user` | public | Create user |
| PUT | `/api/account/edit_user/<uid>` | api_required | Edit user (admin use) |
| DELETE | `/api/account/delete_user/<uid>` | admin_required | Soft-delete user |
| GET | `/api/account/users` | admin_required | Paginated user list (`?page&per_page&search&sort&dir`) |
| POST | `/api/account/<uid>/toggle-verified` | admin_required | Toggle verified status |
| POST | `/api/account/<uid>/disconnect` | admin_required | Force logout user |
| POST | `/api/account/bulk-verify` | admin_required | Bulk verify `{ ids, verified }` |
| POST | `/api/account/bulk-disconnect` | admin_required | Bulk force logout `{ ids }` |
| GET | `/api/account/roles` | admin_required | List all roles |
| PUT | `/api/account/admin/user/<uid>` | admin_required | Admin full edit (role, email, verified…) |
| GET | `/api/account/user-activity/<uid>` | admin_required | 30-day activity chart data |

### `/api/config` — User preferences

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/config/` | api_required | Get current user config (theme, nav…) |
| PATCH | `/api/config/` | api_required | Update config fields |

### `/api/admin` — Site configuration

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/admin/site-config` | admin_required | All site config key-values |
| POST | `/api/admin/site-config` | admin_required | Update a config key `{ key, value }` |

### `/api/log` — Application logs

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/log/` | admin_required | Paginated logs (`?page&per_page&search&category&level&sort&dir&actor_id`) |
| DELETE | `/api/log/<uuid>` | admin_required | Delete one log entry |
| POST | `/api/log/bulk-delete` | admin_required | Delete multiple logs `{ uuids }` |

---

## Architecture patterns

### Route / Core / API split

- **Route** (`<feature>.py`): HTTP only — parse form/JSON, flash, redirect. Zero DB.
- **Core** (`<feature>_core.py`): all DB logic, returns `(obj, msg)`. Logs here.
- **API** (`app/api/<feature>_api.py`): flask-restx Resources. Calls core + verification.
- **Verification** (`verification_<feature>.py`): pure input validation, no ORM.

### Access decorators

```python
# HTML
@admin_required          # or @login_required
@feature_required('key')
def my_view(): ...

# API Resource
method_decorators = [admin_required]  # or [api_required]
```

### Deletion pattern

```python
# Soft delete (user action)
item.is_active = False; item.deleted_at = now(); item.deleted_by = uid

# Hard delete (admin, from trash only)
db.session.delete(item)
```

Always filter active: `Model.query.filter_by(is_active=True)`.  
Trash: `Model.query.filter_by(is_active=False)`.

### Background jobs

Operations on >50 objects or >2 s → background job. Endpoint returns `202 + job_id`. Frontend polls `/api/jobs/<id>`.

---

## JS conventions

- `constants.js` exports: `TOAST`, `CSRF_TOKEN`, `apiFetch(url, method, body)`
- `toaster.js` exports: `create_message(text, TOAST.*, sticky)`
- Always check `res.ok`; use `create_message()` for all feedback — success and error.
- Jinja expressions in `<script>` always quoted: `const id = '{{ current_user.id }}'`

---

## CSS conventions

- Colors: `var(--bg-body)`, `var(--text-main)`, etc. — never hardcoded.
- Dark mode: `[data-bs-theme="dark"]` only.
- One file per feature: `static/css/<feature>/<feature>.css`, loaded via `{% block head_extra %}`.
- Classes prefixed by feature name: `.account-card`, `.admin-badge`, …
- Sections delimited: `/*---SECTION_NAME---*/`

---

## Page template skeleton

```jinja
{% extends 'base.html' %}
{% block head_extra %}{# feature CSS here #}{% endblock %}
{% block content %}
<div class="page-wrapper" v-cloak>
    <loading-bar :active="!page_is_loading"></loading-bar>
    <div v-if="page_is_loading">
        <div class="page-header">
            <div>
                <nav aria-label="breadcrumb"><ol class="breadcrumb mb-1">...</ol></nav>
                <h1 class="page-title">Title</h1>
            </div>
            <div class="page-actions">...</div>
        </div>
        <div class="page-body">...</div>
    </div>
</div>
{% endblock %}
{% block script %}
<script type="module">
    const { createApp, ref, onMounted } = Vue
    import { TOAST, apiFetch } from '../static/js/constants.js'
    import { create_message, display_toast, message_list } from '../static/js/toaster.js'
    import LoadingBar from '../static/js/components/loading-bar.js'
    import Pagination from '../static/js/components/pagination.js'

    createApp({
        delimiters: ['[[', ']]'],
        components: { LoadingBar, Pagination },
        setup() {
            const page_is_loading = ref(false)
            onMounted(async () => {
                await Promise.all([/* fetch calls */])
                page_is_loading.value = true
            })
            return { message_list, page_is_loading }
        }
    }).mount('#main-container')
</script>
{% endblock %}
```

---

## DataTable component

Props: `columns`, `items`, `total-items`, `current-page`, `total-pages`,  
`can-create`, `can-edit`, `can-delete`, `can-detail`, `selectable`, `bulk-actions`, `all-items-ids`

Events: `@sort-change`, `@filter-change`, `@page-change`, `@row-click`,  
`@select-all-pages`, `@bulk-action`, `@create`, `@edit`, `@delete`, `@detail`

Slot: `#row-detail="{ item }"` — content shown in expanded row.

---

## Naming conventions

| Element | Convention |
|---|---|
| URL route | `kebab-case` |
| Blueprint / Namespace | `snake_case_blueprint` / `snake_case_ns` |
| Python function / variable | `snake_case` |
| Python class / model | `PascalCase` |
| Vue component name | `PascalCase` |
| Vue component tag / JS file | `kebab-case` |
| CSS class | `kebab-case` prefixed by feature |
| JS variable | `camelCase` |
| JS constant | `UPPER_SNAKE_CASE` |

---

## Feature checklist (9 blocks)

### 1. Structure
- [ ] `app/features/<f>/__init__.py`, `<f>.py`, `<f>_core.py`, `form.py`
- [ ] `app/api/<f>_api.py`, `verification_<f>.py`
- [ ] `app/static/css/<f>/<f>.css`
- [ ] `app/templates/<f>/` (breadcrumb + page_is_loading on each)
- [ ] `tests/<f>/__init__.py`, `tests/<f>/test_<f>.py`

### 2. Model
- [ ] All standard fields present (id, uuid, title, …, meta)
- [ ] `uuid` auto-generated, `is_public=False` by default
- [ ] Migration: `./launch.sh --migrate "..."` then `./launch.sh --upgrade`

### 3. Access
- [ ] `@login_required` / `@admin_required` + `@feature_required` on every route
- [ ] `method_decorators` on every API Resource
- [ ] FeatureFlag seeded: `key='<f>'`, `enabled=True`

### 4. CRUD
- [ ] HTML: list, detail (`/<uuid>`), create, edit, delete
- [ ] API: GET, POST, PUT, DELETE + restore + hard-delete + bulk
- [ ] Corbeille route: `/admin/<f>/trash`

### 5. Logs
- [ ] `log_action` in create, edit, delete, restore, hard_delete, every bulk + sensitive action

### 6. Jobs
- [ ] Any op >50 objects or >2 s → job, endpoint returns `202 + job_id`

### 7. Tests
- [ ] HTML routes (200/302/403/404 per role), API (201/400/403/404), security fields
- [ ] Trash flow: delete → restore → hard delete
- [ ] `./launch.sh --test` passes

### 8. Docs
- [ ] Update `CLAUDE.md` project layout
- [ ] Update `README.md`

### 9. Security
- [ ] All user fields validated (see validators.py)
- [ ] `bandit -r app/` clean (no HIGH/MEDIUM)
- [ ] No sensitive data in logs or API responses

---

## Security quick-ref

| Threat | Defense |
|---|---|
| SQL injection | SQLAlchemy ORM — never raw `db.execute()` with strings |
| XSS | Jinja2 auto-escape — never `{{ var \| safe }}` on user data |
| CSRF | Flask-WTF on all HTML routes |
| Passwords | bcrypt via `User.password` setter |
| Sessions | Flask-Session server-side |

Validators in `app/core/utils/validators.py`: `is_valid_email`, `is_safe_string`, `sanitize_html`, `is_valid_uuid`.

---

## Test users (conftest.py)

| Email | Password | API Key | Role |
|---|---|---|---|
| `admin@admin.admin` | `admin` | `admin_api_key` | Admin |
| `editor@editor.editor` | `editor` | `editor_api_key` | Editor |
| `read@read.read` | `read` | `read_api_key` | Read Only |
