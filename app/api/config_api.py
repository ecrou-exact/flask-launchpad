from flask import request
from flask_restx import Namespace, Resource

from ..core.utils.decorators import api_required
from ..features.config.config_core import get_user_config, update_config_core
from .verification_config import VerifConfig

config_ns = Namespace('config', description='User interface preferences')


@config_ns.route('/')
class ConfigResource(Resource):
    method_decorators = [api_required]

    def get(self):
        config = get_user_config()
        if not config:
            return {'message': 'No config found'}, 404
        return config.to_json(), 200

    def patch(self):
        if not request.json:
            return {'message': 'Please give data'}, 400
        verif = VerifConfig.verif_update(request.json)
        if 'message' in verif:
            return verif, 400
        config, msg = update_config_core(verif)
        if not config:
            return {'message': msg}, 400
        return {'message': msg, 'config': config.to_json()}, 200
