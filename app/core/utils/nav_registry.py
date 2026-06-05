"""
nav_registry.py — Single source of truth for all navigation items.

To add a new section to the nav + search bar:
  1. Add an entry to NAV below.
  2. That's it. Nav, search bar, and sidebar all update automatically.

Permission values:
  None         → visible to all authenticated users
  'admin_only' → visible only if role.admin = True
  'key'        → visible if user has that permission key (or is admin)
"""

NAV: list[dict] = [

    # ── Navigation (all authenticated users) ──────────────────────────────
    {
        'group':      'Navigation',
        'label':      'Home',
        'icon':       'fa-house',
        'href':       '/',
        'permission': None,
    },
    {
        'group':      'Navigation',
        'label':      'Account',
        'icon':       'fa-user',
        'href':       '/account/',
        'permission': None,
    },
    {
        'group':      'Navigation',
        'label':      'Settings',
        'icon':       'fa-gear',
        'href':       '/settings',
        'permission': None,
    },

    # ── Admin ─────────────────────────────────────────────────────────────
    {
        'group':      'Admin',
        'label':      'Users',
        'icon':       'fa-users',
        'href':       '/admin/users',
        'permission': 'users.view',
    },
    {
        'group':      'Admin',
        'label':      'Roles',
        'icon':       'fa-shield-halved',
        'href':       '/admin/roles',
        'permission': 'admin.roles',
    },
    {
        'group':      'Admin',
        'label':      'Logs',
        'icon':       'fa-scroll',
        'href':       '/admin/logs',
        'permission': 'logs.view',
    },
    {
        'group':      'Admin',
        'label':      'Server Settings',
        'icon':       'fa-server',
        'href':       '/admin/settings',
        'permission': 'admin_only',
    },
    {
        'group':      'Admin',
        'label':      'API Docs',
        'icon':       'fa-code',
        'href':       '/api/',
        'permission': 'admin_only',
        'external':   True,
    },

    # ── Community ─────────────────────────────────────────────────────────────
    {
        'group':      'Community',
        'label':      'Forum',
        'icon':       'fa-comments',
        'href':       '/comments/',
        'permission': 'comments.view',
    },

]


def get_nav_for_user(is_admin: bool, perms: list[str]) -> list[dict]:
    """Return the nav items visible to a user with the given permissions."""
    result = []
    for item in NAV:
        p = item.get('permission')
        visible = (
            p is None
            or is_admin
            or (p != 'admin_only' and p in perms)
        )
        if visible:
            result.append(item)
    return result
