from flask import Blueprint, render_template
from flask_login import login_required

from ...core.utils.decorators import admin_required
from ...core.db_class.site_config import get_site_bool

admin_blueprint = Blueprint('admin', __name__)


@admin_blueprint.route('/users')
@login_required
@admin_required
def users():
    allow_registration = get_site_bool('allow_registration', default=True)
    allow_login        = get_site_bool('allow_login',        default=True)
    return render_template(
        'admin/users.html',
        allow_registration=allow_registration,
        allow_login=allow_login,
    )


@admin_blueprint.route('/users/<int:uid>')
@login_required
@admin_required
def user_detail(uid):
    from ...core.db_class.user import User
    from ...features.account.account_core import get_all_roles
    user  = User.query.get_or_404(uid)
    roles = get_all_roles()
    return render_template('admin/user_detail.html', user=user, roles=roles)


@admin_blueprint.route('/logs')
@login_required
@admin_required
def logs():
    return render_template('admin/logs.html')
