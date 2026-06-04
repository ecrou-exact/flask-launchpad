from flask import abort

from ...core.db_class.user import User, Role


def get_user_or_404(uid: int) -> User:
    user = User.query.get(uid)
    if not user:
        abort(404)
    return user


def get_role_or_404(role_id: int) -> Role:
    role = Role.query.get(role_id)
    if not role:
        abort(404)
    return role
