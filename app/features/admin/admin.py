from flask import Blueprint, render_template
from flask_login import login_required

from ...core.utils.decorators import admin_required

admin_blueprint = Blueprint('admin', __name__)


@admin_blueprint.route('/users')
@login_required
@admin_required
def users():
    return render_template('admin/users.html')
