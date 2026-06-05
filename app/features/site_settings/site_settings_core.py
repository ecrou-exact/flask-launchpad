"""
site_settings_core.py — Read/write .env, expose system info.

All functions return (value, message) or a plain dict.
No Flask imports except current_app (used inside request context only).
"""
import os
import re
import sys
import secrets
import platform


def _env_path() -> str:
    from flask import current_app
    return os.path.normpath(os.path.join(current_app.root_path, '..', '.env'))


# ── .env read/write ───────────────────────────────────────────────────────────

def _read_env_file() -> dict:
    path = _env_path()
    result: dict = {}
    if not os.path.exists(path):
        return result
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, _, v = line.partition('=')
                result[k.strip()] = v.strip()
    return result


def _write_env_file(updates: dict) -> None:
    path  = _env_path()
    env   = _read_env_file()
    env.update({k.upper(): str(v) for k, v in updates.items()})
    with open(path, 'w') as f:
        for k, v in env.items():
            f.write(f"{k}={v}\n")


# ── SMTP ──────────────────────────────────────────────────────────────────────

def get_smtp_config() -> dict:
    return {
        'smtp_host':       os.environ.get('SMTP_HOST', ''),
        'smtp_port':       os.environ.get('SMTP_PORT', '587'),
        'smtp_user':       os.environ.get('SMTP_USER', ''),
        'smtp_sender':     os.environ.get('SMTP_SENDER', ''),
        'smtp_use_tls':    os.environ.get('SMTP_USE_TLS', '1') == '1',
        'smtp_configured': bool(
            os.environ.get('SMTP_HOST', '').strip()
            and os.environ.get('SMTP_USER', '').strip()
        ),
    }


def save_smtp_config_core(data: dict) -> tuple:
    _FIELDS = {
        'smtp_host':     'SMTP_HOST',
        'smtp_port':     'SMTP_PORT',
        'smtp_user':     'SMTP_USER',
        'smtp_password': 'SMTP_PASSWORD',
        'smtp_sender':   'SMTP_SENDER',
        'smtp_use_tls':  'SMTP_USE_TLS',
    }
    updates = {}
    for field, env_key in _FIELDS.items():
        if field in data and data[field] is not None:
            val = str(data[field])
            updates[env_key] = val
            os.environ[env_key] = val  # live effect — no restart needed for SMTP

    _write_env_file(updates)
    return True, "SMTP configuration saved"


# ── Session key ───────────────────────────────────────────────────────────────

def regenerate_session_key_core() -> tuple:
    key = secrets.token_hex(32)
    _write_env_file({'SECRET_KEY': key})
    # os.environ update so the preview reflects the new key immediately
    os.environ['SECRET_KEY'] = key
    return key, "Session key regenerated — restart required to apply"


# ── Package management ───────────────────────────────────────────────────────

def get_installed_packages() -> list:
    """Return all installed packages sorted by name (case-insensitive)."""
    try:
        import importlib.metadata as meta
        dists = sorted(meta.distributions(), key=lambda d: (d.metadata.get('Name') or '').lower())
        result = []
        for d in dists:
            name    = d.metadata.get('Name') or ''
            version = d.metadata.get('Version') or ''
            if name:
                result.append({'name': name, 'version': version})
        return result
    except Exception:
        return []


def _validate_package_name(name: str) -> bool:
    """Only allow safe package names: letters, digits, hyphens, underscores, dots."""
    return bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._\-]{0,99}$', name.strip()))


def update_package_core(name: str) -> tuple:
    """Run pip install --upgrade <name>. Returns (ok, output)."""
    import subprocess
    if not _validate_package_name(name):
        return False, "Invalid package name"
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', name],
            capture_output=True, text=True, timeout=120,
        )
        ok     = result.returncode == 0
        output = (result.stdout.strip() or result.stderr.strip())
        output = output[-500:] if len(output) > 500 else output
        return ok, output
    except Exception as e:
        return False, str(e)


def install_package_core(name: str) -> tuple:
    """Run pip install <name>. Returns (ok, output)."""
    import subprocess
    if not _validate_package_name(name):
        return False, "Invalid package name"
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', name],
            capture_output=True, text=True, timeout=120,
        )
        ok     = result.returncode == 0
        output = (result.stdout.strip() or result.stderr.strip())
        output = output[-500:] if len(output) > 500 else output
        return ok, output
    except Exception as e:
        return False, str(e)


# ── System info ───────────────────────────────────────────────────────────────

def get_system_info() -> dict:
    import flask
    from flask import current_app

    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    db_uri_safe = re.sub(r':[^:@/]+@', ':***@', db_uri)

    key = os.environ.get('SECRET_KEY', '')
    if len(key) >= 8:
        key_preview = key[:4] + '••••••••' + key[-4:]
    elif key:
        key_preview = '••••••••'
    else:
        key_preview = 'not set'

    from ...core.utils.mailer import is_smtp_configured

    return {
        'python_version':     sys.version.split()[0],
        'flask_version':      flask.__version__,
        'platform':           f"{platform.system()} {platform.release()}",
        'debug_mode':         current_app.debug,
        'env':                os.environ.get('FLASKENV', 'development'),
        'db_uri':             db_uri_safe,
        'secret_key_preview': key_preview,
        'secret_key_set':     bool(key),
        'smtp_configured':    is_smtp_configured(),
    }
