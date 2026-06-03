from flask import request
from flask_restx import Namespace, Resource, fields
from sqlalchemy import or_

from .. import db
from ..core.db_class.user import User, Role
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


@account_ns.route('/users')
class ListUsers(Resource):
    """Paginated list of all users — admin only."""
    method_decorators = [admin_required]

    _ALLOWED_SORTS = {'id', 'first_name', 'last_name', 'email', 'created_at', 'role_id'}

    def get(self):
        # ── Query params ────────────────────────────────────────────────
        try:
            page     = max(1, int(request.args.get('page', 1)))
            per_page = min(100, max(1, int(request.args.get('per_page', 10))))
        except (TypeError, ValueError):
            page, per_page = 1, 10

        search   = (request.args.get('search') or '').strip()
        sort_key = request.args.get('sort', 'id')
        sort_dir = request.args.get('dir', 'asc')

        if sort_key not in self._ALLOWED_SORTS:
            sort_key = 'id'
        if sort_dir not in ('asc', 'desc'):
            sort_dir = 'asc'

        # ── Query ────────────────────────────────────────────────────────
        q = db.session.query(User)

        if search:
            like = f'%{search}%'
            q = q.filter(or_(
                User.first_name.ilike(like),
                User.last_name.ilike(like),
                User.email.ilike(like),
                User.username.ilike(like),
            ))

        sort_col = getattr(User, sort_key)
        q = q.order_by(sort_col.asc() if sort_dir == 'asc' else sort_col.desc())

        total       = q.count()
        total_pages = max(1, (total + per_page - 1) // per_page)
        page        = min(page, total_pages)
        users       = q.offset((page - 1) * per_page).limit(per_page).all()

        # ── Serialise ────────────────────────────────────────────────────
        def _role(user):
            r = Role.query.get(user.role_id) if user.role_id else None
            return {'id': r.id, 'name': r.name, 'admin': r.admin} if r else None

        from datetime import datetime, timedelta
        online_threshold = datetime.utcnow() - timedelta(minutes=10)

        items = []
        for u in users:
            role = _role(u)
            items.append({
                'id':              u.id,
                'first_name':      u.first_name,
                'last_name':       u.last_name,
                'email':           u.email,
                'username':        u.username,
                'role_id':         u.role_id,
                'role_name':       role['name'] if role else None,
                'is_admin':        role['admin'] if role else False,
                'avatar_filename': u.avatar_filename,
                'created_at':      u.created_at.isoformat() if u.created_at else None,
                'bio':             u.bio,
                'job_title':       u.job_title,
                'company':         u.company,
                'location':        u.location,
                'is_verified':     u.is_verified,
                'is_connected':    bool(u.last_seen_at and u.last_seen_at >= online_threshold),
                'last_seen_at':    u.last_seen_at.isoformat() if u.last_seen_at else None,
            })

        return {
            'items':       items,
            'total':       total,
            'page':        page,
            'per_page':    per_page,
            'total_pages': total_pages,
        }, 200


@account_ns.route('/<int:uid>/toggle-verified')
class ToggleVerified(Resource):
    method_decorators = [admin_required]

    def post(self, uid):
        user = AccountCore.get_user(uid)
        if not user:
            return {'message': 'User not found'}, 404
        user.is_verified = not user.is_verified
        db.session.commit()
        return {'is_verified': user.is_verified, 'message': 'Updated'}, 200


@account_ns.route('/<int:uid>/disconnect')
class DisconnectUser(Resource):
    method_decorators = [admin_required]

    def post(self, uid):
        user = AccountCore.get_user(uid)
        if not user:
            return {'message': 'User not found'}, 404
        user.force_logout = True
        db.session.commit()
        return {'message': 'User disconnected'}, 200


@account_ns.route('/bulk-verify')
class BulkVerify(Resource):
    method_decorators = [admin_required]

    def post(self):
        data = request.get_json(silent=True) or {}
        ids      = data.get('ids', [])
        verified = bool(data.get('verified', True))
        if not ids:
            return {'message': 'No ids provided'}, 400
        User.query.filter(User.id.in_(ids)).update(
            {'is_verified': verified}, synchronize_session=False
        )
        db.session.commit()
        return {'message': f'Updated {len(ids)} user(s)'}, 200


@account_ns.route('/bulk-disconnect')
class BulkDisconnect(Resource):
    method_decorators = [admin_required]

    def post(self):
        data = request.get_json(silent=True) or {}
        ids = data.get('ids', [])
        if not ids:
            return {'message': 'No ids provided'}, 400
        User.query.filter(User.id.in_(ids)).update(
            {'force_logout': True}, synchronize_session=False
        )
        db.session.commit()
        return {'message': f'Disconnected {len(ids)} user(s)'}, 200
