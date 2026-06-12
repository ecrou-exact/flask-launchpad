from flask import request, send_file
from flask_restx import Namespace, Resource
from flask_login import current_user

from ..core.utils.decorators import api_require_permission
from ..features.site_settings.database_core import (
    get_db_info,
    list_backups,
    create_backup_core,
    delete_backup_core,
    initiate_restore_core,
    confirm_restore_core,
    execute_sql_core,
    get_db_history,
    _safe_backup_path,
)

database_ns = Namespace('database', description='Database management (admin only)')


@database_ns.route('/info')
class DBInfo(Resource):
    method_decorators = [api_require_permission('admin_only')]

    def get(self):
        return get_db_info(), 200


@database_ns.route('/backups')
class DBBackups(Resource):
    method_decorators = [api_require_permission('admin_only')]

    def get(self):
        return list_backups(), 200

    def post(self):
        name, msg = create_backup_core(current_user.id)
        if name:
            return {'filename': name, 'message': msg}, 201
        return {'message': msg}, 400


@database_ns.route('/backups/<string:filename>')
class DBBackup(Resource):
    method_decorators = [api_require_permission('admin_only')]

    def delete(self, filename):
        ok, msg = delete_backup_core(filename, current_user.id)
        return {'message': msg}, 200 if ok else 400


@database_ns.route('/backups/<string:filename>/download')
class DBBackupDownload(Resource):
    method_decorators = [api_require_permission('admin_only')]

    def get(self, filename):
        p = _safe_backup_path(filename)
        if p is None or not p.exists():
            return {'message': 'Backup not found'}, 404
        return send_file(str(p), as_attachment=True, download_name=filename)


@database_ns.route('/restore/initiate')
class DBRestoreInitiate(Resource):
    method_decorators = [api_require_permission('admin_only')]

    def post(self):
        data     = request.get_json(silent=True) or {}
        filename = (data.get('filename') or '').strip()
        if not filename:
            return {'message': 'filename required'}, 400
        ok, msg = initiate_restore_core(filename, current_user.id)
        return {'message': msg}, 200 if ok else 400


@database_ns.route('/restore/confirm')
class DBRestoreConfirm(Resource):
    method_decorators = [api_require_permission('admin_only')]

    def post(self):
        data     = request.get_json(silent=True) or {}
        filename = (data.get('filename') or '').strip()
        code     = (data.get('code')     or '').strip()
        if not filename or not code:
            return {'message': 'filename and code required'}, 400
        ok, msg = confirm_restore_core(filename, code, current_user.id)
        return {'message': msg}, 200 if ok else 400


@database_ns.route('/sql')
class DBSql(Resource):
    method_decorators = [api_require_permission('admin_only')]

    def post(self):
        data  = request.get_json(silent=True) or {}
        query = (data.get('query') or '').strip()
        if not query:
            return {'message': 'query required'}, 400
        ok, result = execute_sql_core(query, current_user.id)
        if ok:
            return result, 200
        return {'message': result}, 400


@database_ns.route('/history')
class DBHistory(Resource):
    method_decorators = [api_require_permission('admin_only')]

    def get(self):
        return get_db_history(100), 200
