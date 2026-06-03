from flask import request
from flask_restx import Namespace, Resource, fields

from ..core.utils.decorators import api_required, admin_required
from ..core.utils.utils import get_user_api
from ..features.account import account_core as AccountCore
from . import verification_api as VerifApi

account_ns = Namespace('account', description='User account management')

_add_model = account_ns.model('AddUser', {
    'first_name': fields.String(required=True),
    'last_name':  fields.String(required=True),
    'email':      fields.String(required=True),
    'password':   fields.String(required=True),
})

_edit_model = account_ns.model('EditUser', {
    'first_name':      fields.String,
    'last_name':       fields.String,
    'email':           fields.String,
    'bio':             fields.String,
    'phone':           fields.String,
    'job_title':       fields.String,
    'company':         fields.String,
    'location':        fields.String,
    'website':         fields.String,
    'social_twitter':  fields.String,
    'social_github':   fields.String,
    'social_linkedin': fields.String,
})


@account_ns.route('/me')
class Me(Resource):
    method_decorators = [api_required]

    def get(self):
        user = get_user_api(request.headers.get('X-API-KEY'))
        if not user:
            return {'message': 'User not found'}, 404
        return user.to_json(), 200

    @account_ns.expect(_edit_model)
    def put(self):
        if not request.json:
            return {'message': 'Please give data'}, 400
        user = get_user_api(request.headers.get('X-API-KEY'))
        verif = VerifApi.verif_edit_user(request.json, user.id)
        if 'message' in verif:
            return verif, 400
        u, msg = AccountCore.edit_user_core(verif, user.id)
        return {'message': msg}, 200 if u else 400


@account_ns.route('/me/reload-api-key')
class ReloadApiKey(Resource):
    method_decorators = [api_required]

    def post(self):
        user = get_user_api(request.headers.get('X-API-KEY'))
        u, msg = AccountCore.reload_api_key_core(user.id)
        if u:
            return {'message': msg, 'api_key': u.api_key}, 200
        return {'message': msg}, 400


@account_ns.route('/user/<int:uid>')
class GetUser(Resource):
    method_decorators = [api_required]

    def get(self, uid):
        user = AccountCore.get_user(uid)
        if user:
            return user.to_json(), 200
        return {'message': 'User not found'}, 404


@account_ns.route('/add_user')
class AddUser(Resource):
    # public — no api_required so admin can create users from external tools
    @account_ns.expect(_add_model)
    def post(self):
        if not request.json:
            return {'message': 'Please give data'}, 400
        verif = VerifApi.verif_add_user(request.json)
        if 'message' in verif:
            return verif, 400
        user, _ = AccountCore.create_user_core(verif)
        if user:
            return {'message': 'User created', 'id': user.id}, 201
        return {'message': 'Error creating user'}, 400


@account_ns.route('/edit_user/<int:uid>')
class EditUser(Resource):
    method_decorators = [api_required]

    @account_ns.expect(_edit_model)
    def put(self, uid):
        if not request.json:
            return {'message': 'Please give data'}, 400
        if not AccountCore.get_user(uid):
            return {'message': 'User not found'}, 404
        verif = VerifApi.verif_edit_user(request.json, uid)
        if 'message' in verif:
            return verif, 400
        u, msg = AccountCore.edit_user_core(verif, uid)
        return {'message': msg}, 200 if u else 400


@account_ns.route('/delete_user/<int:uid>')
class DeleteUser(Resource):
    method_decorators = [admin_required]

    def delete(self, uid):
        caller = get_user_api(request.headers.get('X-API-KEY'))
        if caller and caller.id == uid:
            return {'message': 'Cannot delete your own account'}, 403
        if not AccountCore.get_user(uid):
            return {'message': 'User not found'}, 404
        ok = AccountCore.delete_user_core(uid)
        return {'message': 'User deleted' if ok else 'Error'}, 200 if ok else 400
