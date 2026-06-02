# Flask Launchpad — Codebase Guide

## Rules at a glance

Règles non-négociables à garder en tête à chaque session. La référence complète est dans les sections ci-dessous.

**Commandes** — tout passe par `./launch.sh`. Jamais `python app.py` ou `flask` directement.

**Chaque nouvelle feature** doit couvrir les 9 blocs : structure · modèle · accès · CRUD · logs · jobs · tests · docs · sécurité. Voir checklist complète plus bas.

**Modèle** — tout modèle a : `id`, `uuid` (auto, exposé dans les URLs), `title`, `description`, `is_public` (False), `created_at`, `updated_at`, `created_by`, `is_active`, `deleted_at`, `deleted_by`, `meta`.

**Routes** — jamais de DB dans une route. Toujours : `form_to_dict()` → `*_core()` → flash/redirect.

**Core** — toujours retourner `(objet, "message")`. Logs dans le core, jamais dans les routes.

**Accès** — `@login_required` + `@admin_required` + `@feature_required('key')` sur chaque route. Aucune route sans décorateur explicite.

**Suppression** — jamais physique depuis une action user. `is_active=False` + corbeille admin. Hard delete uniquement depuis `/admin/<feature>/trash`.

**URLs** — UUID dans les liens publics, jamais l'id entier. Les routes acceptent les deux via `get_by_id_or_uuid()`.

**JS** — Composition API, ES modules, `[[...]]`, `TOAST.*` + `apiFetch()` de `constants.js`, jamais `console.log`.

**CSS** — `var(--bg-body)` / `var(--text-main)` — jamais de couleur en dur. Un fichier par feature dans `static/css/<feature>/`.

**Tableaux** — toujours `<data-table>` avec sort/filter/bulk/pagination/expand. Jamais de table from scratch.

**Graphiques** — toujours Apache ECharts encapsulé dans un composant `chart-<type>.js`. Référence : https://echarts.apache.org/examples/en/index.html

**Sécurité** — `bandit -r app/` + `safety check` avant livraison. Tester XSS, injection, champ vide, oversized sur chaque champ user. Jamais `{{ var | safe }}` sur données utilisateur.

**Docs** — mettre à jour `CLAUDE.md` + `README.md` à chaque feature.

---

## What this project is

A Flask boilerplate/starter kit (named "P'tit Crolle" in the UI). It provides a ready-to-use foundation with user authentication, role management, and a REST API. The goal is to clone this and build a new app on top of it.

## Running the app

Toutes les commandes passent par `./launch.sh`. Ne jamais appeler `python app.py` ou `flask` directement.

| Command | Description |
|---|---|
| `./launch.sh --setup` | Premier lancement : venv, dépendances, config, init DB |
| `./launch.sh --start` | Démarre le serveur de développement |
| `./launch.sh --test` | Lance la suite de tests (`pytest`) |
| `./launch.sh --test -v tests/account/` | Tests ciblés avec options pytest |
| `./launch.sh --migrate "message"` | Crée un fichier de migration Alembic |
| `./launch.sh --upgrade` | Applique les migrations en attente |
| `./launch.sh --downgrade` | Annule la dernière migration |
| `./launch.sh --migration-info` | Affiche la révision courante et l'historique |
| `./launch.sh --backup-db` | Sauvegarde la DB dans `backups/` |
| `./launch.sh --reload-db` | Drop + recrée la DB (propose backup/restore) |
| `./launch.sh --deploy` | Backup → git pull → pip install → check migrations |
| `./launch.sh --help` | Affiche l'aide |

Default dev server: `http://127.0.0.1:7009`  
Default admin credentials: `admin@admin.admin` / `admin`

## Project layout

```
app/
  __init__.py              # App factory (create_app), extension init, blueprint registration

  api/
    api.py                 # api_blueprint — mounts flask-restx, registers namespaces
    account_api.py         # REST endpoints for account (flask-restx Resources)
    verification_api.py    # Input validation for account API payloads

  core/
    db_class/
      user.py              # All SQLAlchemy models: User, Role, AnonymousUser
    utils/
      decorators.py        # @admin_required, @api_required, @login_required
      utils.py             # Shared helpers: form_to_dict, generate_api_key, get_user_api
      init_db.py           # Seed functions: create_admin(), create_user_test()

  features/
    home/
      home.py              # home_blueprint — the "/" route
    account/
      account.py           # account_blueprint — HTML routes (login, register, edit, logout)
      account_core.py      # DB logic: get_user, create_user_core, edit_user_core
      form.py              # WTForms form classes

  templates/
    base.html              # Single base template — all pages extend this
    home.html
    account/               # Account-specific templates
    macros/
      _flashes.html        # Flash messages (Bootstrap toasts)
      form_macros.html     # WTForms rendering macros
    utils/
      403.html / 404.html / 500.html

  static/
    css/
      core.css             # Global styles, CSS custom properties, dark mode
      login.css            # Login page specific styles
    js/
      theme.js             # Dark/light mode logic (loaded sync before CSS)
      blur.js              # API key blur/reveal toggle
      toaster.js           # Vue toast system (create_message, display_toast)
      components/
        loading-bar.js     # Vue loading bar component
        pagination.js      # Vue pagination component
    image/
      crolle.png
    bootstrap-5.3.0/
    fontawesome-6.3.0/

app.py                     # Entry point: CLI args (--init_db / --recreate_db / --delete_db), error handlers
config.py(.default)        # Config classes — copy .default to config.py
tests/
  conftest.py              # pytest fixtures (app, client, runner) — testing config + SQLite
  account/
    test_account.py
```

## Architecture patterns

### Feature structure

Each feature lives in `app/features/<feature>/` with this exact split:

| File | Role |
|---|---|
| `<feature>.py` | Blueprint + routes. Only HTTP: parse form/JSON, flash, redirect, render. Never touches the DB. |
| `<feature>_core.py` | All DB logic. Receives plain dicts, returns `(object, message)` tuples. |
| `form.py` | WTForms form classes. |

API layer lives separately in `app/api/`:

| File | Role |
|---|---|
| `<feature>_api.py` | flask-restx `Resource` classes. Calls `*_core` and `verification_api`. |
| `verification_api.py` | Pure input validation for API payloads. No ORM calls from routes. |

### DB models — `app/core/db_class/user.py`

All models in one file. The `db` SQLAlchemy instance comes from `app/__init__.py`.

Current models: `User`, `Role`, `AnonymousUser` (flask-login anonymous proxy).

`User` methods: `is_admin()`, `read_only()`, `username()`, `verify_password()`, `to_json()`

### REST API — `/api/`

Built with **flask-restx**. Swagger UI at `/api/`.

Authentication: `X-API-KEY` header validated by `@api_required` against `User.api_key`.

CSRF is exempted for the entire `api_blueprint`.

To add a new namespace: create `app/api/<feature>_api.py` with a `Namespace`, then `api.add_namespace(ns, path="/<feature>")` in `api.py`.

### Decorators

- `@login_required` — flask-login, redirects to `account.login`
- `@admin_required` — HTML routes check `current_user`, API routes check `X-API-KEY`
- `@api_required` — API key presence + validity

## Config

Copy `config.py.default` to `config.py`. Selected by `FLASKENV` env var.

- `development`: SQLite (`ptitcrolle.sqlite`), debug on, server-side sessions in SQLAlchemy
- `testing`: separate SQLite, CSRF disabled, used by pytest

## Testing

```bash
pytest
```

`conftest.py` seeds three test users per session:
- `admin@admin.admin` / `admin` — role_id 1 (Admin)
- `editor@editor.editor` / `editor` — role_id 2 (Editor)
- `read@read.read` / `read` — role_id 3 (Read Only)

## Adding a new feature — checklist

1. Create `app/features/<feature>/` with `__init__.py`, `<feature>.py`, `<feature>_core.py`, `form.py`.
2. Add models to `app/core/db_class/user.py`.
3. Register the blueprint in `app/__init__.py`.
4. Run `./launch.sh --migrate "add <feature>"` then `./launch.sh --upgrade`.
5. Add templates under `app/templates/<feature>/`, each extending `base.html`.
6. Add `app/api/<feature>_api.py` + `app/api/verification_api.py` (toujours — pas optionnel).
7. Register the namespace in `app/api/api.py`.
8. Add access decorators on every route and Resource (see Contrôle d'accès).
9. Create `tests/<feature>/test_<feature>.py` with tests HTML + API + par rôle.

---

## Contrôle d'accès

Chaque route et chaque Resource API doit déclarer explicitement son niveau d'accès. Aucune route ne reste sans décorateur sauf si elle est intentionnellement publique — dans ce cas, ajouter un commentaire `# public`.

### Niveaux disponibles

| Niveau | Route HTML | Resource API |
|---|---|---|
| Public | _(aucun décorateur)_ `# public` | _(aucun)_ `# public` |
| Authentifié | `@login_required` | `method_decorators = [api_required]` |
| Admin seulement | `@admin_required` | `method_decorators = [admin_required]` |

### Routes HTML

```python
# public
@account_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    ...

# authentifié
@account_blueprint.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_user():
    ...

# admin seulement
@feature_blueprint.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin_panel():
    ...
```

### API Resources

```python
# authentifié
class GetItem(Resource):
    method_decorators = [api_required]
    def get(self, id): ...

# admin seulement
class DeleteItem(Resource):
    method_decorators = [admin_required]
    def delete(self, id): ...

# public
class PublicStats(Resource):
    # public
    def get(self): ...
```

---

## Tests

### Structure des fichiers

```
tests/
  conftest.py              # fixtures globales — ne pas modifier
  <feature>/
    __init__.py            # vide
    test_<feature>.py      # tests HTML + API + par rôle
```

Créer le dossier et le `__init__.py` à chaque nouvelle feature.

### Utilisateurs de test disponibles (via conftest)

| Email | Password | API Key | Rôle |
|---|---|---|---|
| `admin@admin.admin` | `admin` | `admin_api_key` | Admin |
| `editor@editor.editor` | `editor` | `editor_api_key` | Editor |
| `read@read.read` | `read` | `read_api_key` | Read Only |

### Pattern de test

Chaque fichier de test couvre trois cas : route HTML, endpoint API, et vérification des droits par rôle.

```python
# tests/<feature>/test_<feature>.py

def login_as(client, email, password):
    return client.post('/account/login', data={'email': email, 'password': password}, follow_redirects=True)


# ── HTML routes ──────────────────────────────────────────────────────────────

def test_index_requires_login(client):
    res = client.get('/feature/')
    assert res.status_code == 302  # redirect to login

def test_index_as_admin(client):
    login_as(client, 'admin@admin.admin', 'admin')
    res = client.get('/feature/')
    assert res.status_code == 200

def test_index_forbidden_for_readonly(client):
    login_as(client, 'read@read.read', 'read')
    res = client.get('/feature/admin')
    assert res.status_code == 403


# ── API endpoints ────────────────────────────────────────────────────────────

def test_api_get_item(client):
    res = client.get('/api/feature/item/1',
        headers={'X-API-KEY': 'admin_api_key'})
    assert res.status_code == 200

def test_api_create_item(client):
    res = client.post('/api/feature/add',
        content_type='application/json',
        headers={'X-API-KEY': 'admin_api_key'},
        json={'name': 'test', 'description': 'test'})
    assert res.status_code == 201

def test_api_forbidden_without_key(client):
    res = client.get('/api/feature/item/1')
    assert res.status_code == 403

def test_api_forbidden_for_non_admin(client):
    res = client.delete('/api/feature/item/1',
        headers={'X-API-KEY': 'read_api_key'})
    assert res.status_code == 403
```

Lancer les tests : `./launch.sh --test` ou `./launch.sh --test -v tests/<feature>/`

---

## Outils externes comme composants Vue

Toute bibliothèque JS externe (chart, éditeur de texte, carte, etc.) est **obligatoirement** encapsulée dans un composant Vue dans `static/js/components/`. Ne jamais l'appeler directement dans un template.

### Règle

```
✓  import MonOutil from '../static/js/components/mon-outil.js'
✗  new MonOutil(document.getElementById('...'), ...)  ← direct dans le template
```

### Exemple : encapsuler Chart.js

```javascript
// static/js/components/line-chart.js
import { ref, onMounted } from 'vue'   // si Vue 3 SFC, sinon utiliser Vue global

export default {
    name: 'LineChart',
    props: {
        data:    { type: Object, required: true },
        options: { type: Object, default: () => ({}) },
    },
    template: `<canvas ref="canvas"></canvas>`,
    setup(props) {
        const canvas = ref(null)
        onMounted(() => {
            new Chart(canvas.value, { type: 'line', data: props.data, options: props.options })
        })
        return { canvas }
    }
}
```

Utilisation dans le template :

```html
<line-chart :data="chart_data" :options="chart_options"></line-chart>
```

### Composants disponibles

| Fichier | Composant | Props | Events |
|---|---|---|---|
| `loading-bar.js` | `<loading-bar>` | `:active` (Boolean) | — |
| `pagination.js` | `<pagination>` | `:current-page`, `:total-pages` | `@change-page` |
| `data-table.js` | `<data-table>` | voir ci-dessous | voir ci-dessous |

---

## Composant DataTable — standard obligatoire

Tout tableau de données dans l'app utilise `<data-table>`. Ne jamais coder un tableau from scratch.

### Props

| Prop | Type | Défaut | Description |
|---|---|---|---|
| `columns` | Array | requis | Définition des colonnes `[{ key, label, sortable?, truncate? }]` |
| `items` | Array | `[]` | Données de la page courante |
| `total-items` | Number | `0` | Nombre total d'items (toutes pages) |
| `current-page` | Number | `1` | Page courante |
| `total-pages` | Number | `1` | Nombre total de pages |
| `can-create` | Boolean | `false` | Affiche le bouton Create |
| `can-edit` | Boolean | `false` | Affiche le bouton Edit par ligne |
| `can-delete` | Boolean | `false` | Affiche le bouton Delete par ligne |
| `can-detail` | Boolean | `false` | Affiche le bouton Detail par ligne |
| `selectable` | Boolean | `false` | Active la sélection de lignes + bulk actions |
| `bulk-actions` | Array | `[]` | Actions bulk `[{ key, label, icon?, variant? }]` |
| `all-items-ids` | Array | `[]` | Rempli par le parent après `@select-all-pages` |

### Events

| Event | Payload | Déclencheur |
|---|---|---|
| `@sort-change` | `{ key, dir }` | Clic sur un en-tête de colonne sortable |
| `@filter-change` | `query` (String) | Saisie dans le champ search |
| `@page-change` | `page` (Number) | Clic sur la pagination |
| `@row-click` | `item` | Clic sur une ligne (expand/collapse détail) |
| `@select-all-pages` | — | Clic sur "Select all N items" — le parent doit fetcher tous les IDs et passer `:all-items-ids` |
| `@bulk-action` | `{ action, ids }` | Clic sur une action bulk |
| `@create` | — | Clic sur Create |
| `@edit` | `item` | Clic sur Edit |
| `@delete` | `item` | Clic sur Delete |
| `@detail` | `item` | Clic sur Detail |

### Slot

`#row-detail="{ item }"` — contenu affiché dans la ligne expandée au clic. Si non fourni, affiche toutes les colonnes en grille.

### Comportement attendu

- **Tri** : clic sur un en-tête sortable → icône `fa-sort` / `fa-sort-up` / `fa-sort-down`, émet `@sort-change`
- **Recherche** : input avec bouton reset, émet `@filter-change`
- **Expansion** : clic sur une ligne → ligne de détail s'ouvre en dessous (slot `#row-detail`)
- **Sélection page** : checkbox en-tête → sélectionne/désélectionne tous les items de la page courante
- **Sélection globale** : quand toute la page est cochée, bandeau "Select all N items" → clic → émet `@select-all-pages` → parent fetche tous les IDs → les passe via `:all-items-ids`
- **Bulk bar** : apparaît dès qu'un item est sélectionné, affiche le compte + les actions bulk + bouton Clear
- **Empty state** : ligne "No results" avec icône quand `items` est vide
- **Permissions** : les boutons Edit/Delete/Create/Detail n'apparaissent que si les props `can-*` sont `true` — le parent calcule ces booleans selon le rôle de `current_user`

### Exemple d'utilisation

```html
<data-table
    :columns="columns"
    :items="items"
    :total-items="total_items"
    :current-page="current_page"
    :total-pages="total_pages"
    :can-create="is_admin"
    :can-edit="true"
    :can-delete="is_admin"
    :can-detail="true"
    :selectable="true"
    :bulk-actions="[{ key: 'delete', label: 'Delete', icon: 'fa-trash', variant: 'danger' }]"
    :all-items-ids="all_ids"
    @sort-change="handleSort"
    @filter-change="handleFilter"
    @page-change="handlePageChange"
    @row-click="handleRowClick"
    @select-all-pages="fetchAllIds"
    @bulk-action="handleBulkAction"
    @create="openCreateModal"
    @edit="openEditModal"
    @delete="confirmDelete"
    @detail="openDetail">
    <template #row-detail="{ item }">
        <div class="row g-2">
            <div class="col-12 col-md-4">
                <small class="text-muted d-block">Created at</small>
                <span>[[ item.created_at ]]</span>
            </div>
        </div>
    </template>
</data-table>
```

```javascript
const columns = [
    { key: 'name',  label: 'Name',  sortable: true,  truncate: true },
    { key: 'email', label: 'Email', sortable: true,  truncate: true },
    { key: 'role',  label: 'Role',  sortable: false, truncate: false },
]

const all_ids  = ref([])

async function fetchAllIds() {
    const res = await apiFetch('/api/feature/all-ids')
    const data = await res.json()
    all_ids.value = data.ids
}

function handleBulkAction({ action, ids }) {
    if (action === 'delete') {
        // apiFetch('/api/feature/bulk-delete', 'POST', { ids })
    }
}
```

---

## CSS par feature

Chaque feature a son propre fichier CSS. Ne jamais écrire le CSS d'une feature dans `core.css`.

### Structure

```
app/static/css/
  core.css                  # styles globaux uniquement
  login.css                 # exception : page standalone
  <feature>/
    <feature>.css           # styles spécifiques à la feature
```

Exemple pour une feature `inventory` :

```
app/static/css/
  inventory/
    inventory.css
```

### Chargement

Le fichier CSS de la feature est chargé dans **chaque template** de cette feature via `{% block head_extra %}` :

```jinja
{% block head_extra %}
<link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='css/inventory/inventory.css') }}">
{% endblock %}
```

### Contenu du fichier CSS feature

Toutes les classes sont **préfixées par le nom de la feature** pour éviter les collisions :

```css
/*---INVENTORY_CARDS---*/

.inventory-card { ... }
.inventory-card-title { ... }
.inventory-badge { ... }

/*---INVENTORY_TABLE---*/

.inventory-table-status { ... }
```

---

## Table de nommage globale

Référence unique pour nommer chaque type d'élément dans le projet.

| Élément | Convention | Exemple |
|---|---|---|
| **URL de route** | `kebab-case` | `/inventory/edit-item` |
| **Blueprint** | `snake_case + _blueprint` | `inventory_blueprint` |
| **Namespace API** | `snake_case + _ns` | `inventory_ns` |
| **Fonction Python** | `snake_case` | `get_item_core()` |
| **Classe Python / Modèle** | `PascalCase` | `InventoryItem` |
| **Fichier Python** | `snake_case` | `inventory_core.py` |
| **Fichier template** | `snake_case` | `item_list.html` |
| **Fichier CSS feature** | `kebab-case` | `inventory.css` |
| **Classe CSS** | `kebab-case préfixé feature` | `.inventory-card` |
| **Fichier composant Vue** | `kebab-case` | `stock-chart.js` |
| **Nom composant Vue** | `PascalCase` | `StockChart` |
| **Tag HTML composant** | `kebab-case` | `<stock-chart>` |
| **Variable JS** | `camelCase` | `currentPage` |
| **Fonction JS** | `camelCase` | `fetchItems()` |
| **Constante JS** | `UPPER_SNAKE_CASE` | `TOAST.SUCCESS` |

---

## Système de logs

Chaque action significative dans l'app est enregistrée. Jamais de nom en dur dans un log — toujours des IDs ou UUIDs.

### Modèle `Log`

```python
class Log(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    action     = db.Column(db.String(64), nullable=False)  # 'create', 'edit', 'delete', 'login', ...
    object_type= db.Column(db.String(64), nullable=True)   # 'user', 'inventory_item', ...
    object_id  = db.Column(db.String(36), nullable=True)   # UUID ou id — jamais le nom
    actor_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    details    = db.Column(db.JSON, nullable=True)          # données supplémentaires (dict)
    is_public  = db.Column(db.Boolean, default=False)       # True = visible par tous / False = admin only
```

### Visibilité

| `is_public` | Qui peut voir |
|---|---|
| `True` | Tous les utilisateurs authentifiés |
| `False` | Admins uniquement |

### Fonction centrale `log_action`

```python
# app/core/utils/logs.py
def log_action(action, object_type=None, object_id=None, details=None, is_public=False):
    from flask import request
    from flask_login import current_user

    actor_id = current_user.id if current_user.is_authenticated else None
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    log = Log(
        action=action,
        object_type=object_type,
        object_id=str(object_id) if object_id else None,
        actor_id=actor_id,
        ip_address=ip,
        details=details,
        is_public=is_public,
    )
    db.session.add(log)
    db.session.commit()
```

### Actions standard

| Action | `object_type` | `is_public` | Déclencheur |
|---|---|---|---|
| `login` | `user` | `False` | Connexion réussie |
| `logout` | `user` | `False` | Déconnexion |
| `create` | `<feature>` | `True` | Création d'un objet |
| `edit` | `<feature>` | `True` | Modification d'un objet |
| `delete` | `<feature>` | `False` | Suppression d'un objet |
| `bulk_delete` | `<feature>` | `False` | Suppression de masse |
| `bulk_edit` | `<feature>` | `False` | Modification de masse |

### Règle d'utilisation

Appeler `log_action` dans la couche `*_core.py` après chaque opération réussie. Jamais dans les routes ni dans l'API.

```python
# ✓ — dans feature_core.py
def create_item_core(form_dict) -> tuple:
    try:
        item = Item(...)
        db.session.add(item)
        db.session.commit()
        log_action('create', 'item', item.id, details={'name': item.name}, is_public=True)
        return item, "Item created"
    except Exception:
        return None, "Error creating item"

# ✗ — jamais dans une route ou un endpoint API
@item_blueprint.route('/create')
def create():
    log_action(...)   # interdit ici
```

### Details : toujours des IDs, jamais des noms

```python
# ✓
log_action('edit', 'user', user.id, details={'role_id': role.id})

# ✗ — jamais de noms en dur
log_action('edit', 'user', user.id, details={'role': 'Admin', 'username': 'John Doe'})
```

### Checklist par feature

À chaque nouvelle feature, ajouter `log_action` pour :
- [ ] Création d'un objet
- [ ] Modification d'un objet
- [ ] Suppression d'un objet
- [ ] Toute action bulk
- [ ] Toute action sensible (changement de rôle, accès admin, etc.)

---

## Système de jobs background

Les opérations longues ou de masse ne bloquent jamais la requête HTTP. Elles sont déléguées à un job background.

### Règle : quand utiliser un job

| Cas | Traitement |
|---|---|
| Opération sur > 50 objets | Job background |
| Durée estimée > 2 secondes | Job background |
| Export / import de données | Job background |
| Suppression / modification en masse | Job background |
| Envoi d'emails en masse | Job background |
| Opération unitaire rapide | Traitement direct |

### Modèle `Job`

```python
import uuid

class Job(db.Model):
    id         = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    type       = db.Column(db.String(64), nullable=False)    # 'bulk_delete_item', 'export_csv', ...
    status     = db.Column(db.String(16), default='pending') # pending / running / done / failed
    actor_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    params     = db.Column(db.JSON, nullable=True)           # input du job (IDs, filtres...)
    result     = db.Column(db.JSON, nullable=True)           # résultat (nb traités, erreurs...)
    error      = db.Column(db.Text, nullable=True)           # message d'erreur si failed
    progress   = db.Column(db.Integer, default=0)            # 0-100
```

### Pattern côté API

L'endpoint retourne immédiatement un `job_id` avec `202 Accepted`. Ne jamais bloquer en attendant la fin.

```python
# ✓ — endpoint qui crée un job
class BulkDeleteItem(Resource):
    method_decorators = [admin_required]
    def post(self):
        ids = request.json.get('ids', [])
        job, msg = create_job_core('bulk_delete_item', params={'ids': ids})
        return {'message': msg, 'job_id': job.id}, 202

# ✗ — ne jamais traiter en synchrone
class BulkDeleteItem(Resource):
    def post(self):
        for id in ids:
            delete_item(id)   # bloque la requête
        return {'message': 'done'}, 200
```

### Pattern côté frontend

Le frontend lance le job puis poll le statut jusqu'à `done` ou `failed`.

```javascript
async function launchBulkDelete(ids) {
    const res = await apiFetch('/api/feature/bulk-delete', 'POST', { ids })
    if (!res.ok) { await display_toast(res); return }

    const { job_id } = await res.json()
    await create_message('Job started...', TOAST.WARNING, false)
    pollJob(job_id)
}

async function pollJob(job_id) {
    const interval = setInterval(async () => {
        const res = await apiFetch(`/api/jobs/${job_id}`)
        const job = await res.json()

        if (job.status === 'done') {
            clearInterval(interval)
            await create_message('Operation complete', TOAST.SUCCESS, false)
            fetchItems()  // rafraîchit la table
        } else if (job.status === 'failed') {
            clearInterval(interval)
            await create_message(job.error || 'Job failed', TOAST.ERROR, true)
        }
    }, 2000)
}
```

### Logs + jobs

Tout job terminé (`done` ou `failed`) enregistre un log :

```python
def run_job(job):
    try:
        # ... traitement ...
        job.status = 'done'
        log_action(job.type, details={'job_id': job.id, 'result': job.result}, is_public=False)
    except Exception as e:
        job.status = 'failed'
        job.error = str(e)
        log_action(job.type + '_failed', details={'job_id': job.id, 'error': str(e)}, is_public=False)
    db.session.commit()
```

### Checklist par feature avec opérations de masse

- [ ] Endpoint retourne `202 + job_id` immédiatement
- [ ] Job enregistré en DB avec `status='pending'`
- [ ] Log créé à la fin du job (succès ou échec)
- [ ] Frontend poll le statut et affiche le résultat via `create_message`
- [ ] Page d'historique des jobs accessible (admin only)

---

## Panel d'administration

L'admin voit tout et peut tout faire. Chaque feature expose une section dans le panel admin.

### Feature flags

Chaque feature peut être activée ou désactivée depuis l'admin sans redéploiement.

#### Modèle `FeatureFlag`

```python
class FeatureFlag(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    key        = db.Column(db.String(64), unique=True, nullable=False)  # 'inventory', 'reporting', ...
    enabled    = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
```

#### Helper `is_feature_enabled`

```python
# app/core/utils/feature_flags.py
def is_feature_enabled(key: str) -> bool:
    flag = FeatureFlag.query.filter_by(key=key).first()
    return flag.enabled if flag else True  # activé par défaut si inexistant
```

#### Ce qui est désactivé quand un flag est `False`

| Élément | Comportement |
|---|---|
| Routes HTML | `abort(404)` — décorateur `@feature_required('key')` |
| Endpoints API | Retournent `{"message": "Feature disabled"}`, `403` |
| Entrées de navigation | Masquées dans le menu |
| Boutons / liens | Masqués dans les templates |

#### Décorateur `@feature_required`

```python
# à ajouter dans decorators.py
def feature_required(key):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not is_feature_enabled(key):
                abort(404)
            return f(*args, **kwargs)
        return decorated
    return decorator
```

```python
# dans la route
@feature_blueprint.route('/')
@login_required
@feature_required('inventory')
def index():
    ...
```

#### Dans les templates

```jinja
{# Masquer un lien de nav si la feature est désactivée #}
{% if is_feature_enabled('inventory') %}
<a href="/inventory">Inventory</a>
{% endif %}
```

Le helper `is_feature_enabled` est injecté dans le contexte Jinja via un context processor dans `create_app()`.

### Rôles et permissions admin

L'accès à l'admin est réservé aux utilisateurs avec `role.admin = True`. Les rôles existants :

| Rôle | `admin` | `read_only` | Accès admin |
|---|---|---|---|
| Admin | `True` | `False` | Complet |
| Editor | `False` | `False` | Aucun |
| Read Only | `False` | `True` | Aucun |

Toute route du panel admin porte `@admin_required`. Toute API admin porte `method_decorators = [admin_required]`.

### Checklist admin par feature

À chaque nouvelle feature :
- [ ] Créer un `FeatureFlag` seedé avec `key='<feature>'`, `enabled=True`
- [ ] Ajouter `@feature_required('<feature>')` sur toutes les routes de la feature
- [ ] Masquer les liens de navigation avec `{% if is_feature_enabled('<feature>') %}`
- [ ] Ajouter un toggle dans le panel admin pour activer/désactiver la feature
- [ ] Ajouter une section dans l'admin pour gérer les données de la feature (CRUD + logs + jobs)

---

## Graphiques — Apache ECharts

Toute représentation graphique utilise **Apache ECharts**. Aucune autre librairie de charts n'est autorisée.

Référence des exemples : https://echarts.apache.org/examples/en/index.html

### Règle

ECharts ne s'utilise jamais directement dans un template. Chaque type de graphique est encapsulé dans un composant Vue dédié dans `static/js/components/`.

```
static/js/components/
  chart-line.js       # courbes / séries temporelles
  chart-bar.js        # barres verticales ou horizontales
  chart-pie.js        # camembert / donut
  chart-graph.js      # graphe de relations
  ...
```

### Structure d'un composant ECharts

```javascript
// static/js/components/chart-line.js
const { ref, onMounted, onUnmounted, watch } = Vue

export default {
    name: 'ChartLine',
    props: {
        option:  { type: Object, required: true },  // option ECharts complète
        height:  { type: String, default: '300px' },
        loading: { type: Boolean, default: false },
    },
    template: `<div ref="el" :style="{ width: '100%', height: height }"></div>`,
    setup(props) {
        const el = ref(null)
        let chart = null

        onMounted(() => {
            chart = echarts.init(el.value)
            chart.setOption(props.option)
            window.addEventListener('resize', () => chart.resize())
        })

        watch(() => props.option, (opt) => {
            if (chart) chart.setOption(opt)
        }, { deep: true })

        watch(() => props.loading, (val) => {
            if (!chart) return
            val ? chart.showLoading() : chart.hideLoading()
        })

        onUnmounted(() => {
            window.removeEventListener('resize', () => chart.resize())
            chart?.dispose()
        })

        return { el }
    }
}
```

### Utilisation dans un template

```html
<chart-line :option="chart_option" height="350px" :loading="!page_is_loading">
</chart-line>
```

```javascript
import ChartLine from '../static/js/components/chart-line.js'

// Dans setup()
const chart_option = ref({
    xAxis: { type: 'category', data: ['Jan', 'Feb', 'Mar'] },
    yAxis: { type: 'value' },
    series: [{ data: [120, 200, 150], type: 'line' }]
})
```

### Règles ECharts

- Toujours passer l'`option` complète en prop — le composant ne connaît pas le domaine métier
- Toujours réagir au resize avec `window.addEventListener('resize', () => chart.resize())`
- Toujours disposer le chart avec `chart.dispose()` dans `onUnmounted`
- Afficher `showLoading()` pendant les fetches via le prop `:loading`
- Nommer les composants `chart-<type>` en kebab-case

---

## Checklist obligatoire — toute nouvelle feature

**Cette checklist s'applique à chaque demande de feature sans exception.** Rien ne peut être livré sans que chaque point soit coché.

### 1. Structure

- [ ] `app/features/<feature>/__init__.py`
- [ ] `app/features/<feature>/<feature>.py` — routes avec décorateurs d'accès
- [ ] `app/features/<feature>/<feature>_core.py` — logique DB
- [ ] `app/features/<feature>/form.py` — WTForms
- [ ] `app/api/<feature>_api.py` — endpoints REST
- [ ] `app/api/verification_<feature>.py` — validation API
- [ ] `app/static/css/<feature>/<feature>.css` — styles de la feature
- [ ] `app/templates/<feature>/` — templates (breadcrumb + page_is_loading sur chacun)
- [ ] `tests/<feature>/__init__.py`
- [ ] `tests/<feature>/test_<feature>.py`

### 2. Modèle

- [ ] Champs : `id`, `uuid`, `title`, `description`, `is_public`, `created_at`, `updated_at`, `created_by`, `is_active`, `deleted_at`, `deleted_by`, `meta`
- [ ] `uuid` généré automatiquement (`default=lambda: str(uuid.uuid4())`)
- [ ] `is_public = False` par défaut
- [ ] Migration : `./launch.sh --migrate "<feature>: add <model>"` puis `./launch.sh --upgrade`

### 3. Accès et feature flag

- [ ] `@login_required` / `@admin_required` sur chaque route
- [ ] `@feature_required('<feature>')` sur chaque route
- [ ] `method_decorators` sur chaque Resource API
- [ ] `FeatureFlag` seedé avec `key='<feature>'`, `enabled=True`

### 4. CRUD complet

- [ ] Routes HTML : list, detail (`/<uuid>`), create, edit (`/<uuid>/edit`), delete (`/<uuid>/delete`)
- [ ] API endpoints : GET, POST, PUT, DELETE + restore + hard-delete + bulk
- [ ] Routes acceptent `id` entier ET `uuid` via `get_by_id_or_uuid()`
- [ ] URLs publiques utilisent toujours l'UUID, jamais l'id entier
- [ ] `is_public` gérable depuis l'admin
- [ ] Corbeille : `delete_core`, `restore_core`, `hard_delete_core`
- [ ] Vue admin corbeille : `/admin/<feature>/trash`

### 5. Logs

- [ ] `log_action('create', ...)` dans `create_*_core`
- [ ] `log_action('edit', ...)` dans `edit_*_core`
- [ ] `log_action('delete', ...)` dans `delete_*_core`
- [ ] `log_action('restore', ...)` dans `restore_*_core`
- [ ] `log_action('hard_delete', ...)` dans `hard_delete_*_core`
- [ ] `log_action(job.type, ...)` à la fin de chaque job

### 6. Jobs background

- [ ] Toute opération > 50 objets ou > 2s utilise un job
- [ ] L'endpoint retourne `202 + job_id`
- [ ] Le frontend poll le statut

### 7. Tests

- [ ] Tests HTML routes (200, 302, 403, 404 selon rôle)
- [ ] Tests API (201, 400, 403, 404 selon clé et rôle)
- [ ] Tests de droits : admin / editor / read_only / anonyme
- [ ] Tests de sécurité sur chaque champ utilisateur (voir section Sécurité)
- [ ] Tests de la corbeille (delete → restore → hard delete)
- [ ] `./launch.sh --test` passe sans erreur

### 8. Documentation

- [ ] Mettre à jour `CLAUDE.md` : ajouter la feature dans le project layout
- [ ] Mettre à jour `README.md` : documenter la feature (usage, endpoints, flags)

### 9. Sécurité

- [ ] Chaque champ user validé (voir section Sécurité)
- [ ] Lancer `bandit` sur les fichiers créés
- [ ] Vérifier qu'aucune donnée sensible ne fuit dans les logs ou les réponses API

---

## Sécurité

La sécurité est non négociable. Tout champ qui reçoit une valeur extérieure est validé et testé.

### Validation des inputs — système réutilisable

Toute validation API passe par `verification_<feature>.py`. Chaque champ est contrôlé :

```python
# app/core/utils/validators.py — helpers réutilisables

import re, bleach

def is_valid_email(value: str) -> bool:
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', value))

def is_safe_string(value: str, max_length: int = 255) -> bool:
    """Refuse les chaînes vides, trop longues, ou avec des caractères de contrôle."""
    return bool(value and len(value) <= max_length and not re.search(r'[\x00-\x1f\x7f]', value))

def sanitize_html(value: str) -> str:
    """Nettoie le HTML — utiliser pour les champs rich text uniquement."""
    return bleach.clean(value, tags=['b','i','u','em','strong','p','br','ul','li'], strip=True)

def is_valid_uuid(value: str) -> bool:
    return bool(re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', value, re.I))
```

### Règles par type de champ

| Type | Validation obligatoire |
|---|---|
| Email | Format regex + unicité DB |
| Mot de passe | Min 8 cars, 1 maj, 1 min, 1 chiffre |
| Texte libre | `is_safe_string()` + longueur max |
| Rich text / HTML | `sanitize_html()` via `bleach` |
| ID / UUID | `is_valid_uuid()` ou cast `int` avec try/except |
| Enum / choix | Vérifier que la valeur est dans la liste autorisée |
| Fichier uploadé | Extension whitelist, taille max, scan MIME type |

### Tests de sécurité obligatoires par feature

Pour chaque champ user d'un endpoint, tester :

```python
# tests/<feature>/test_<feature>_security.py

def test_xss_in_name(client):
    res = client.post('/api/feature/add',
        headers={'X-API-KEY': 'admin_api_key'},
        content_type='application/json',
        json={'name': '<script>alert(1)</script>'})
    assert res.status_code == 400

def test_sql_injection_in_search(client):
    res = client.get("/api/feature/?search=' OR '1'='1",
        headers={'X-API-KEY': 'admin_api_key'})
    assert res.status_code in [200, 400]
    # vérifie que la réponse ne contient pas de données non filtrées

def test_empty_required_field(client):
    res = client.post('/api/feature/add',
        headers={'X-API-KEY': 'admin_api_key'},
        content_type='application/json',
        json={'name': ''})
    assert res.status_code == 400

def test_oversized_field(client):
    res = client.post('/api/feature/add',
        headers={'X-API-KEY': 'admin_api_key'},
        content_type='application/json',
        json={'name': 'A' * 10000})
    assert res.status_code == 400

def test_unauthorized_access(client):
    res = client.get('/api/feature/1')
    assert res.status_code == 403

def test_access_other_user_data(client):
    """Un utilisateur ne peut pas accéder aux données d'un autre."""
    # login as editor, essayer d'accéder à une resource d'un autre user
    res = client.get('/api/feature/1',
        headers={'X-API-KEY': 'editor_api_key'})
    assert res.status_code in [403, 404]
```

### Outils de sécurité

| Outil | Usage | Commande |
|---|---|---|
| `bandit` | Analyse statique du code Python (injections, secrets...) | `bandit -r app/` |
| `safety` | Vérifie les dépendances avec des CVEs connues | `safety check` |
| `bleach` | Sanitisation HTML côté serveur | `pip install bleach` |

Lancer `bandit -r app/` et `safety check` avant chaque livraison. Aucune erreur `HIGH` ou `MEDIUM` ne doit subsister.

### Protections déjà en place (ne pas contourner)

| Protection | Mécanisme |
|---|---|
| CSRF | Flask-WTF sur toutes les routes HTML |
| Injection SQL | SQLAlchemy ORM — ne jamais faire de `db.execute()` avec des strings |
| XSS | Jinja2 auto-escape — ne jamais utiliser `{{ var \| safe }}` sur des données utilisateur |
| Mots de passe | bcrypt via le modèle `User` |
| Sessions | Flask-Session côté serveur |

---

## Philosophie : code extensible et maintenable

Toute décision d'architecture répond à une seule question : **est-ce que je peux modifier ou étendre ça dans 6 mois sans tout casser ?**

### Les features sont des îles

Chaque feature est indépendante. Elle ne communique pas directement avec une autre feature — elle passe par le core.

```
✓  feature_a → core/utils → feature_b_core (via import explicite)
✗  feature_a → feature_b directement (couplage caché)
```

Une feature désactivée ne doit rien casser ailleurs. Si ce n'est pas le cas, le couplage est trop fort.

### Rien n'est codé en dur

Toute valeur qui pourrait changer est une constante, une config, ou un flag :

```python
# ✗ — en dur
if user.role_id == 1:

# ✓ — lisible et modifiable
if user.is_admin():
```

```javascript
// ✗ — en dur
await create_message("ok", "success-subtle")

// ✓ — constante
await create_message("ok", TOAST.SUCCESS)
```

### Concevoir pour l'ajout, pas pour la prévision

Ne pas anticiper des besoins hypothétiques, mais concevoir chaque élément pour qu'on puisse **ajouter** sans **modifier** ce qui existe :

- Un nouveau rôle → ajouter une entrée en DB, pas modifier les décorateurs
- Une nouvelle action bulk → ajouter `{ key, label }` au tableau `bulk-actions`, pas modifier le composant
- Un nouveau type de log → ajouter une action dans le tableau standard, pas modifier `log_action()`
- Un nouveau graphique → créer `chart-xxx.js`, pas modifier un composant existant

### Les modèles anticipent la croissance

Tout modèle inclut ces champs dès le départ, sans exception :

```python
import uuid as _uuid

class Item(db.Model):
    # ── Identifiants ────────────────────────────────────────────────
    id         = db.Column(db.Integer, primary_key=True)
    uuid       = db.Column(db.String(36), unique=True, nullable=False,
                           default=lambda: str(_uuid.uuid4()))

    # ── Contenu standard ────────────────────────────────────────────
    title       = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_public   = db.Column(db.Boolean, default=False)

    # ── Traçabilité ─────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # ── Corbeille ───────────────────────────────────────────────────
    is_active  = db.Column(db.Boolean, default=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # ── Extension future ────────────────────────────────────────────
    meta       = db.Column(db.JSON, nullable=True)
```

**`is_public`** contrôle la visibilité :

| `is_public` | Qui peut voir |
|---|---|
| `False` | Créateur + admins uniquement |
| `True` | Tous les utilisateurs authentifiés |

L'admin peut basculer `is_public` depuis le panel d'administration pour n'importe quel objet.

### Routes accessibles par ID et par UUID

Chaque route qui prend un identifiant accepte indifféremment l'`id` entier ou l'`uuid` :

```python
# app/core/utils/utils.py
def get_by_id_or_uuid(model, identifier):
    try:
        return model.query.filter_by(id=int(identifier), is_active=True).first()
    except (ValueError, TypeError):
        return model.query.filter_by(uuid=identifier, is_active=True).first()
```

```python
# Dans feature_core.py
def get_item(identifier):
    return get_by_id_or_uuid(Item, identifier)
```

```python
# Dans les routes — un seul pattern pour les deux
@feature_blueprint.route('/<identifier>')
@login_required
@feature_required('feature')
def detail(identifier):
    item = FeatureCore.get_item(identifier)
    if not item:
        abort(404)
```

Les URLs publiques exposent toujours l'UUID (jamais l'`id` entier) :

```html
<!-- ✓ -->
<a :href="'/feature/' + item.uuid">View</a>

<!-- ✗ -->
<a :href="'/feature/' + item.id">View</a>
```

### CRUD obligatoire par feature

Chaque feature expose systématiquement ces actions en HTML et en API :

| Action | Route HTML | Endpoint API | Accès |
|---|---|---|---|
| **List** | `GET /<feature>/` | `GET /api/<feature>/` | Selon rôle |
| **Detail** | `GET /<feature>/<uuid>` | `GET /api/<feature>/<uuid>` | Selon rôle |
| **Create** | `GET+POST /<feature>/create` | `POST /api/<feature>/` | Selon rôle |
| **Edit** | `GET+POST /<feature>/<uuid>/edit` | `PUT /api/<feature>/<uuid>` | Selon rôle |
| **Delete** | `POST /<feature>/<uuid>/delete` | `DELETE /api/<feature>/<uuid>` | Selon rôle |
| **Restore** | — | `POST /api/<feature>/<uuid>/restore` | Admin |
| **Hard delete** | — | `DELETE /api/<feature>/<uuid>/hard` | Admin |

### Soft delete et corbeille

Rien n'est jamais supprimé définitivement par une action utilisateur normale. Tout passe par la corbeille. Seul un admin peut vider la corbeille (suppression physique).

#### Champs obligatoires sur chaque modèle

```python
class Item(db.Model):
    # ...
    is_active  = db.Column(db.Boolean, default=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
```

#### Fonctions core obligatoires par feature

```python
def delete_item_core(id) -> tuple:
    """Soft delete — envoie en corbeille."""
    try:
        item = get_item(id)
        item.is_active = False
        item.deleted_at = datetime.utcnow()
        item.deleted_by = current_user.id
        db.session.commit()
        log_action('delete', 'item', item.id, is_public=False)
        return item, "Item moved to trash"
    except Exception:
        return None, "Error deleting item"

def restore_item_core(id) -> tuple:
    """Restaure un item depuis la corbeille."""
    try:
        item = Item.query.get(id)   # pas de filtre is_active
        item.is_active = True
        item.deleted_at = None
        item.deleted_by = None
        db.session.commit()
        log_action('restore', 'item', item.id, is_public=False)
        return item, "Item restored"
    except Exception:
        return None, "Error restoring item"

def hard_delete_item_core(id) -> tuple:
    """Suppression physique — admin only, depuis la corbeille uniquement."""
    try:
        item = Item.query.get(id)
        db.session.delete(item)
        db.session.commit()
        log_action('hard_delete', 'item', item.id, is_public=False)
        return True, "Item permanently deleted"
    except Exception:
        return False, "Error permanently deleting item"
```

#### Requêtes — toujours filtrer

```python
# Données actives (affichage normal)
def get_all_items():
    return Item.query.filter_by(is_active=True).all()

# Corbeille (admin uniquement)
def get_trashed_items():
    return Item.query.filter_by(is_active=False).all()
```

#### Règles

| Action | Qui peut | Résultat |
|---|---|---|
| Supprimer | Selon les droits de la feature | `is_active=False`, `deleted_at`, `deleted_by` remplis |
| Restaurer | Admin | `is_active=True`, champs effacés |
| Supprimer définitivement | Admin uniquement | `db.session.delete()` — irréversible |
| Vider la corbeille | Admin uniquement | Hard delete de tous les items `is_active=False` de la feature |

#### Checklist corbeille par feature

- [ ] Ajouter `is_active`, `deleted_at`, `deleted_by` au modèle
- [ ] Implémenter `delete_*_core`, `restore_*_core`, `hard_delete_*_core`
- [ ] Ajouter route admin `/admin/<feature>/trash` avec liste + restore + hard delete
- [ ] Ajouter endpoint API `GET /api/<feature>/trash` (admin only)
- [ ] Ajouter endpoint API `POST /api/<feature>/restore/<id>` (admin only)
- [ ] Ajouter endpoint API `DELETE /api/<feature>/hard-delete/<id>` (admin only)
- [ ] Logger chaque action (delete, restore, hard_delete)

### Chaque couche ne connaît que la suivante

```
Route  →  Core  →  DB
  ↓         ↓
 Form    log_action
```

- Les routes ne connaissent pas SQLAlchemy
- Les cores ne connaissent pas `request`, `flash`, `redirect`
- Les `verification_api` ne connaissent pas les cores
- Les templates ne connaissent pas l'API

Si une couche doit accéder à une autre en sautant un niveau, c'est un signal que l'architecture doit être revue.

### Une migration = un changement atomique

Chaque `./launch.sh --migrate` correspond à un seul changement logique. Ne jamais grouper des modifications non liées dans une migration.

```bash
# ✓
./launch.sh --migrate "add is_active to item"
./launch.sh --migrate "add meta json to item"

# ✗
./launch.sh --migrate "add fields and fix stuff"
```

### Les tests prouvent l'indépendance

Si une feature ne peut pas être testée en isolation (sans dépendre d'une autre feature), c'est qu'elle est trop couplée. Chaque fichier `test_<feature>.py` tourne seul.

---

## Coding standards

### Python — nommage

- Variables et fonctions : `snake_case`
- Classes : `PascalCase`
- Blueprints : `<feature>_blueprint`
- Namespaces API : `<feature>_ns`
- Ordre des imports : stdlib → third-party → local

### Python — couche routes

Les routes ne touchent **jamais** la DB directement :

```python
# ✓
form_dict = form_to_dict(form)
obj, message = FeatureCore.do_something(form_dict)
flash(message, "success" if obj else "error")
return redirect(...)

# ✗ — interdit dans une route
db.session.add(...)
User.query.filter_by(...)
```

### Python — couche core

Toutes les fonctions `*_core` retournent un tuple `(objet, message)` :

```python
def create_something_core(form_dict) -> tuple:
    try:
        ...
        return obj, "Success"
    except Exception:
        return None, "Error"
```

Les getters simples (`get_user`, `get_all_roles`) peuvent retourner l'objet directement.

### Python — couche API

Structure fixe pour chaque Resource :

```python
def post(self):
    if not request.json:
        return {"message": "Please give data"}, 400
    verif = VerifApi.verif_something(request.json)
    if "message" in verif:
        return verif, 400
    obj, msg = Core.do_something(verif)
    return {"message": msg}, 201
```

### Templates Jinja2

Tout template étend `base.html` :

```jinja
{% extends 'base.html' %}

{% block head_extra %}  {# CSS spécifique à la page uniquement #}
{% endblock %}

{% block top_nav %}{% endblock %}  {# vide = cache le bouton menu #}

{% block content %}
{% endblock %}

{% block script %}  {# Vue app de la page — remplace le script par défaut #}
{% endblock %}
```

Les partiels/macros s'appellent `_nom.html` (underscore prefix).

### JavaScript / Vue 3

- Toujours Composition API (`setup()`)
- Toujours ES modules (`import` / `export default`)
- Délimiteurs Vue : `[[...]]`
- Les toasts passent par `create_message()` de `toaster.js`, jamais en inline
- Les composants réutilisables vont dans `static/js/components/`

```js
// ✓
import { create_message } from '../static/js/toaster.js';
import MonComposant from '../static/js/components/mon-composant.js';
```

### CSS

- Toutes les couleurs via des variables CSS, jamais en dur :

```css
/* ✓ */
background-color: var(--bg-body);
color: var(--text-main);

/* ✗ */
background-color: #212529;
```

- Dark mode exclusivement via `[data-bs-theme="dark"]`
- Classes en `kebab-case`
- Sections délimitées par `/*---NOM_SECTION---*/`
- Classes Bootstrap en priorité, CSS custom uniquement pour ce que Bootstrap ne couvre pas

---

## Conventions HTML / Responsive

### Structure de page

Tout `{% block content %}` suit ce squelette :

```html
<div class="page-wrapper">

    <div class="page-header">
        <h1 class="page-title">Titre</h1>
        <div class="page-actions">
            <button class="btn btn-primary">Action</button>
        </div>
    </div>

    <div class="page-body">
        <!-- contenu -->
    </div>

</div>
```

`page-wrapper`, `page-header`, `page-actions`, `page-body` sont définis dans `core.css` — ils gèrent l'espacement et le responsive.

### Grille responsive

**Mobile-first** : toujours partir du plus petit, ajouter les breakpoints pour monter.

```html
<!-- colonnes -->
<div class="row g-3">
    <div class="col-12 col-md-6 col-lg-4"> ... </div>
</div>

<!-- flex qui change de direction -->
<div class="d-flex flex-column flex-md-row gap-3"> ... </div>

<!-- visibilité -->
<div class="d-none d-md-block"> ... </div>  {# masqué sur mobile #}
<div class="d-md-none"> ... </div>           {# masqué sur desktop #}
```

Jamais de largeur fixe en `px` dans les colonnes — uniquement `col-*`, `w-100`, `w-auto`, ou `max-width` en CSS.

### Texte — règles anti-débordement

Toute donnée dynamique (DB ou saisie utilisateur) est protégée :

```html
<!-- 1 ligne → tronqué avec ... -->
<span class="text-truncate d-block">{{ valeur }}</span>

<!-- multiligne → force le retour à la ligne -->
<p class="text-break">{{ contenu_long }}</p>

<!-- dans un flex : min-w-0 sur le conteneur pour que text-truncate fonctionne -->
<div class="d-flex align-items-center gap-2 min-w-0">
    <span class="text-truncate">{{ texte }}</span>
    <button class="btn btn-sm flex-shrink-0">Action</button>
</div>
```

Les tableaux sont **toujours** dans `.table-responsive`. Les colonnes de texte long ont un `max-width` :

```html
<div class="table-responsive">
    <table class="table">
        <td class="text-truncate" style="max-width: 200px;">{{ valeur }}</td>
    </table>
</div>
```

### Cartes (cards)

Structure fixe :

```html
<div class="card border-0 shadow-sm h-100">
    <div class="card-body">
        <h5 class="card-title text-truncate mb-1">{{ titre }}</h5>
        <p class="card-text text-muted small text-break">{{ description }}</p>
    </div>
    <div class="card-footer bg-transparent d-flex justify-content-end gap-2">
        <a href="#" class="btn btn-sm btn-outline-primary">Voir</a>
    </div>
</div>
```

### Règles CSS custom

- Pas de `style=""` inline sauf valeurs dynamiques Vue (`:style="..."`)
- Pas d'`id` pour styler, uniquement des classes
- Les classes custom suivent le préfixe de la feature : `.account-card`, `.account-header`
- Jamais de taille fixe `px` pour les largeurs

### Classes Bootstrap clés à connaître

| Besoin | Classes |
|---|---|
| Texte tronqué 1 ligne | `text-truncate d-block` |
| Texte long multiligne | `text-break` |
| Flex qui change de sens | `flex-column flex-md-row` |
| Bouton fixe dans un flex | `flex-shrink-0` |
| Conteneur flex pour tronquer | `min-w-0` |
| Masquer sur mobile | `d-none d-md-block` |
| Masquer sur desktop | `d-md-none` |
| Espacement responsive | `p-3 p-md-4`, `gap-2 gap-md-3` |

---

## Template de page par défaut

Toute nouvelle page copie ce squelette. Ne jamais s'en écarter.

```jinja
{% extends 'base.html' %}

{# Page-specific CSS only — leave empty if none #}
{% block head_extra %}
{# <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='css/feature.css') }}"> #}
{% endblock %}

{% block content %}
<div class="page-wrapper" v-cloak>
    <loading-bar :active="!page_is_loading"></loading-bar>

    <div v-if="page_is_loading">

        {# ---- Page header ---- #}
        <div class="page-header">
            <div>
                <nav aria-label="breadcrumb">
                    <ol class="breadcrumb mb-1">
                        <li class="breadcrumb-item"><a href="/">Home</a></li>
                        <li class="breadcrumb-item active">Page Name</li>
                    </ol>
                </nav>
                <h1 class="page-title">Page Title</h1>
            </div>
            <div class="page-actions">
                {# action buttons #}
            </div>
        </div>

        {# ---- Page body ---- #}
        <div class="page-body">
            {# content here #}
        </div>

    </div>
</div>
{% endblock %}

{% block script %}
<script type="module">
    const { createApp, ref, onMounted } = Vue;
    import { message_list, create_message } from '../static/js/toaster.js';
    import Pagination from '../static/js/components/pagination.js';
    import LoadingBar from '../static/js/components/loading-bar.js';

    createApp({
        delimiters: ['[[', ']]'],
        components: { Pagination, LoadingBar },
        setup() {

            // ── Init ────────────────────────────────────────────────
            const page_is_loading = ref(false)

            async function init() {
                await Promise.all([
                    // fetch_something(),
                ])
                page_is_loading.value = true
            }

            onMounted(() => init())

            // ── Pagination ──────────────────────────────────────────
            const current_page = ref(1)
            const total_pages = ref(1)

            function handlePageChange(page) {
                current_page.value = page
                // fetch_something(page)
            }

            // ── Return ──────────────────────────────────────────────
            return {
                message_list,
                page_is_loading,
                current_page,
                total_pages,
                handlePageChange,
            }
        },
    }).mount('#main-container')
</script>
{% endblock %}
```

### Règles de la template

- **`{% block head_extra %}`** : CSS spécifique à la page en haut — jamais de `<style>` inline
- **`v-cloak`** sur `page-wrapper` : cache la page tant que Vue n'est pas monté
- **`page_is_loading`** : tout le contenu visible est enveloppé dans `v-if="page_is_loading"` — la `loading-bar` tourne pendant les fetches initiaux
- **Breadcrumb** : toujours présent, reflète le chemin réel dans l'app (`Home > Section > Page`)
- **`#main-container`** : toujours le point de montage Vue, jamais un autre id
- **Composants** : importer `Pagination` et `LoadingBar` même si la page n'en a pas encore besoin — retirer uniquement si définitivement inutiles
- **Langue** : tout en anglais (variables, commentaires, labels)

---

## Composants UI réutilisables

Toute nouvelle feature utilise **obligatoirement** ces composants. Ne jamais recoder une table, une pagination ou un filtre from scratch.

### LoadingBar

Toujours présent en haut du `page-wrapper`. Tourne tant que `page_is_loading` est `false`.

```html
<loading-bar :active="!page_is_loading"></loading-bar>
<div v-if="page_is_loading">
    <!-- contenu de la page -->
</div>
```

### Table standard

Structure fixe pour toute liste de données :

```html
<div class="table-responsive">
    <table class="table table-hover align-middle mb-0">
        <thead>
            <tr>
                <th class="text-truncate" style="max-width: 200px;">Column</th>
                <th class="text-end">Actions</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="item in items" :key="item.id">
                <td class="text-truncate" style="max-width: 200px;">[[ item.name ]]</td>
                <td class="text-end">
                    <a :href="`/feature/${item.id}`" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-eye"></i>
                    </a>
                </td>
            </tr>
            <tr v-if="!items.length">
                <td colspan="99" class="text-center text-muted py-4">No results</td>
            </tr>
        </tbody>
    </table>
</div>
```

### Pagination

Props : `:current-page` (Number), `:total-pages` (Number). Événement : `@change-page`.

```html
<pagination
    :current-page="current_page"
    :total-pages="total_pages"
    @change-page="handlePageChange">
</pagination>
```

```javascript
const current_page = ref(1)
const total_pages  = ref(1)

function handlePageChange(page) {
    current_page.value = page
    fetchItems(page)
}
```

### Filtre / Recherche

Structure fixe pour tout champ de recherche au-dessus d'une table :

```html
<div class="d-flex flex-column flex-md-row gap-2 mb-3">
    <div class="input-group">
        <span class="input-group-text"><i class="fas fa-search"></i></span>
        <input type="text" class="form-control" placeholder="Search..."
               v-model="search_query" @input="handleSearch">
    </div>
    <button class="btn btn-outline-secondary flex-shrink-0" @click="resetFilters">
        <i class="fas fa-xmark me-1"></i>Reset
    </button>
</div>
```

```javascript
const search_query = ref('')

function handleSearch() {
    current_page.value = 1
    fetchItems()
}

function resetFilters() {
    search_query.value = ''
    fetchItems()
}
```

### Pattern complet : table + filtre + pagination

```html
<div class="page-body">
    <!-- Filter bar -->
    <div class="d-flex flex-column flex-md-row gap-2 mb-3">
        <div class="input-group">
            <span class="input-group-text"><i class="fas fa-search"></i></span>
            <input type="text" class="form-control" placeholder="Search..."
                   v-model="search_query" @input="handleSearch">
        </div>
    </div>

    <!-- Table -->
    <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
            <thead>
                <tr>
                    <th>Name</th>
                    <th class="text-end">Actions</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="item in items" :key="item.id">
                    <td class="text-truncate" style="max-width: 250px;">[[ item.name ]]</td>
                    <td class="text-end">
                        <a :href="`/feature/${item.id}`" class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-eye"></i>
                        </a>
                    </td>
                </tr>
                <tr v-if="!items.length">
                    <td colspan="99" class="text-center text-muted py-4">No results</td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- Pagination -->
    <pagination :current-page="current_page" :total-pages="total_pages"
                @change-page="handlePageChange">
    </pagination>
</div>
```

---

## Règles JavaScript

### Protéger `{{ }}` dans les scripts

VS Code souligne `{{ }}` en erreur dans les blocs `<script>`. Toute expression Jinja dans un contexte JS doit être enveloppée dans des guillemets :

```javascript
// ✓
const userId = '{{ current_user.id }}'
const uploadUrl = '{{ url_for("feature.upload") }}'

// ✗ — VS Code error
const userId = {{ current_user.id }}
```

Dans le HTML (attributs), `{{ }}` est déjà dans des guillemets d'attribut — pas de problème.

### Jamais de `console.log`

Tout feedback visible passe par `create_message`. `console.log` est interdit dans le code livré :

```javascript
// ✓
await create_message("User saved", TOAST.SUCCESS, false)
await create_message("Something went wrong", TOAST.ERROR, true)

// ✗
console.log("user saved")
console.error("something went wrong")
```

### Constantes partagées — `static/js/constants.js`

Un seul fichier de constantes importé dans chaque page :

```javascript
// Toast severity — always use these, never raw strings
export const TOAST = {
    SUCCESS: 'success-subtle',
    WARNING: 'warning-subtle',
    ERROR:   'danger-subtle',
}

// CSRF token (injected by base.html)
export const CSRF_TOKEN = document.getElementById('csrf_token')?.value

// Authenticated JSON fetch — use for every API call
export async function apiFetch(url, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN,
        },
    }
    if (body) options.body = JSON.stringify(body)
    return fetch(url, options)
}
```

Import dans chaque page :

```javascript
import { TOAST, apiFetch } from '../static/js/constants.js'
import { create_message, display_toast } from '../static/js/toaster.js'

// Exemple d'appel API standard
async function fetchUser(id) {
    const res = await apiFetch(`/api/account/user/${id}`)
    if (!res.ok) {
        await create_message("Failed to load user", TOAST.ERROR, true)
        return
    }
    // ...
}
```

### Gestion des erreurs API

Toujours vérifier `res.ok` et utiliser `display_toast` pour les réponses serveur :

```javascript
// ✓
const res = await apiFetch('/api/account/add_user', 'POST', form_data)
if (res.ok) {
    await create_message("User created", TOAST.SUCCESS, false)
} else {
    await display_toast(res)   // affiche le message d'erreur retourné par l'API
}

// ✗ — ne jamais ignorer les erreurs silencieusement
const res = await apiFetch('/api/...')
const data = await res.json()
```
