from functools import wraps

from flask import abort, request
from flask_login import current_user
from .utils import get_user_api, verif_api_key


def permission_required(perm):
    """Restrict a view to users with the given permission."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if perm == "admin":
                if request.path.startswith("/api/"):
                    api_key = request.headers.get("X-API-KEY")
                    if api_key:
                        # API key auth
                        user = get_user_api(api_key)
                        if not user or not user.is_admin():
                            abort(403)
                    elif current_user.is_authenticated and current_user.is_admin():
                        # Session auth (internal frontend calls via apiFetch)
                        pass
                    else:
                        abort(403)
                elif not current_user.is_admin():
                    abort(403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def verification_required():
    """Restrict an api access to users without a key"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.path.startswith("/api/") and verif_api_key(request.headers):
                abort(403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(f):
    return permission_required("admin")(f)

def api_required(f):
    return verification_required()(f)

