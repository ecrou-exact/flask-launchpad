"""
permissions.py — Central permission registry.

To add a new permission:
  1. Add an entry to PERMISSIONS below.
  2. That's it. It appears in the role editor UI automatically.

To protect a route:
  @permission_required('users.edit')
  def my_view(): ...

Admins (role.admin = True) bypass all permission checks.
"""

PERMISSIONS: dict[str, dict] = {

    # ── Admin ──────────────────────────────────────────────────────────────
    'admin.site_config': {
        'label':       'Manage site settings',
        'description': 'Change site-wide config (registration, login lock…)',
        'group':       'Admin',
        'icon':        'fa-sliders',
    },
    'admin.server_settings': {
        'label':       'Server settings',
        'description': 'Access SMTP, session key and system info (admin only by default).',
        'group':       'Admin',
        'icon':        'fa-server',
    },
    'admin.roles': {
        'label':       'Manage roles',
        'description': 'Create, edit and delete roles and their permissions.',
        'group':       'Admin',
        'icon':        'fa-shield-halved',
    },

    # ── Users ───────────────────────────────────────────────────────────────
    'users.view': {
        'label':       'View users',
        'description': 'See the user list and public profiles.',
        'group':       'Users',
        'icon':        'fa-users',
    },
    'users.edit': {
        'label':       'Edit users',
        'description': 'Edit profiles, roles, and verification status.',
        'group':       'Users',
        'icon':        'fa-user-pen',
    },
    'users.delete': {
        'label':       'Delete users',
        'description': 'Remove user accounts.',
        'group':       'Users',
        'icon':        'fa-user-minus',
    },

    # ── Logs ────────────────────────────────────────────────────────────────
    'logs.view': {
        'label':       'View logs',
        'description': 'Access the application log viewer.',
        'group':       'Logs',
        'icon':        'fa-scroll',
    },
    'logs.delete': {
        'label':       'Delete logs',
        'description': 'Delete individual or bulk log entries.',
        'group':       'Logs',
        'icon':        'fa-trash',
    },

    # ── Comments ─────────────────────────────────────────────────────────────
    'comments.view': {
        'label':       'View comments',
        'group':       'Comments',
        'icon':        'fa-comments',
    },
    'comments.create': {
        'label':       'Post comments',
        'group':       'Comments',
        'icon':        'fa-comment-plus',
    },
    'comments.edit_own': {
        'label':       'Edit own comments',
        'group':       'Comments',
        'icon':        'fa-comment-pen',
    },
    'comments.delete_own': {
        'label':       'Delete own comments',
        'group':       'Comments',
        'icon':        'fa-comment-minus',
    },
    'comments.moderate': {
        'label':       'Moderate comments',
        'description': 'Delete/restore any comment, see private comments',
        'group':       'Comments',
        'icon':        'fa-shield-check',
    },

}


def get_by_group() -> dict[str, list]:
    """Return permissions grouped by their 'group' key, preserving insertion order."""
    groups: dict[str, list] = {}
    for key, perm in PERMISSIONS.items():
        g = perm.get('group', 'Other')
        if g not in groups:
            groups[g] = []
        groups[g].append({'key': key, **perm})
    return groups


def all_keys() -> list[str]:
    return list(PERMISSIONS.keys())
