from flask import Blueprint, render_template
from ...core.utils.decorators import require_permission

site_settings_blueprint = Blueprint('site_settings', __name__)


@site_settings_blueprint.route('/', strict_slashes=False)
@require_permission('admin_only')
def index():
    return render_template('site_settings/index.html')
