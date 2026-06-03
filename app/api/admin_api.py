from flask import request
from flask_restx import Namespace, Resource

from ..core.utils.decorators import admin_required
from ..core.db_class.site_config import SiteConfig, get_site_bool, set_site_value
from flask_login import current_user

admin_ns = Namespace('admin', description='Admin-only site configuration')

_ALLOWED_KEYS = {'allow_registration', 'allow_login'}


@admin_ns.route('/site-config')
class SiteConfigList(Resource):
    method_decorators = [admin_required]

    def get(self):
        rows = SiteConfig.query.all()
        return {r.key: {'value': r.value, 'label': r.label} for r in rows}, 200

    def post(self):
        data = request.get_json(silent=True) or {}
        key   = data.get('key', '').strip()
        value = data.get('value')

        if key not in _ALLOWED_KEYS:
            return {'message': f'Unknown key. Allowed: {sorted(_ALLOWED_KEYS)}'}, 400
        if value is None:
            return {'message': 'value is required'}, 400

        uid = current_user.id if current_user.is_authenticated else None
        set_site_value(key, '1' if value else '0', user_id=uid)
        return {'key': key, 'value': str(value), 'message': 'Updated'}, 200
