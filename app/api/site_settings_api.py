from flask import request
from flask_restx import Namespace, Resource
from flask_login import current_user

from ..core.utils.decorators import api_require_permission
from ..core.utils.logger import log_action, api_category
from ..features.site_settings.site_settings_core import (
    get_system_info,
    get_smtp_config,
    save_smtp_config_core,
    regenerate_session_key_core,
)

site_settings_ns = Namespace('site-settings', description='Server & environment configuration')


@site_settings_ns.route('/system')
class SystemInfo(Resource):
    method_decorators = [api_require_permission('admin_only')]

    def get(self):
        return get_system_info(), 200


@site_settings_ns.route('/smtp')
class SmtpConfig(Resource):
    method_decorators = [api_require_permission('admin_only')]

    def get(self):
        return get_smtp_config(), 200

    def post(self):
        data = request.get_json(silent=True) or {}
        ok, msg = save_smtp_config_core(data)
        if ok:
            log_action(
                "SMTP config updated",
                "smtp_config_update",
                category=api_category('admin'),
                level="info",
                object_type="smtp_config",
                is_public=False,
                meta={
                    'smtp_host': data.get('smtp_host', ''),
                    'smtp_port': data.get('smtp_port', ''),
                    'smtp_user': data.get('smtp_user', ''),
                },
            )
        return {'message': msg}, 200 if ok else 400


@site_settings_ns.route('/smtp/test')
class SmtpTest(Resource):
    method_decorators = [api_require_permission('admin_only')]

    def post(self):
        import os
        data = request.get_json(silent=True) or {}
        to   = data.get('to', '').strip()
        if not to:
            uid = current_user.id if current_user.is_authenticated else None
            if uid:
                from ..core.db_class.user import User
                u  = User.query.get(uid)
                to = u.email if u else ''
        if not to:
            return {'message': 'No recipient email provided', 'steps': []}, 400

        host    = os.environ.get('SMTP_HOST', '').strip()
        port    = os.environ.get('SMTP_PORT', '587').strip()
        user    = os.environ.get('SMTP_USER', '').strip()
        sender  = os.environ.get('SMTP_SENDER', '').strip() or user
        use_tls = os.environ.get('SMTP_USE_TLS', '1').strip() == '1'

        steps = [
            f"Recipient   : {to}",
            f"SMTP host   : {host or '(not set)'}",
            f"SMTP port   : {port}",
            f"SMTP user   : {user or '(not set)'}",
            f"Sender      : {sender or '(not set)'}",
            f"Encryption  : {'STARTTLS' if use_tls else 'SSL/TLS'}",
        ]

        from ..core.utils.mailer import send_test_email
        ok, msg = send_test_email(to)

        steps.append(f"Result      : {'✓ ' if ok else '✗ '}{msg}")

        log_action(
            f"SMTP test {'succeeded' if ok else 'failed'}: {msg}",
            "smtp_test",
            category=api_category('admin'),
            level="success" if ok else "warning",
            object_type="smtp_config",
            is_public=False,
            meta={'to': to, 'host': host, 'port': port, 'ok': ok, 'error': msg if not ok else None},
        )

        return {'message': msg, 'steps': steps, 'ok': ok}, 200 if ok else 400


@site_settings_ns.route('/session-key')
class SessionKey(Resource):
    method_decorators = [api_require_permission('admin_only')]

    def post(self):
        _, msg = regenerate_session_key_core()
        log_action(
            "Session key regenerated",
            "session_key_regenerate",
            category=api_category('admin'),
            level="warning",
            object_type="site_settings",
            is_public=False,
        )
        return {'message': msg}, 200


@site_settings_ns.route('/packages')
class PackageList(Resource):
    method_decorators = [api_require_permission('admin_only')]

    def get(self):
        """Return all installed Python packages, with optional ?q= search filter."""
        from ..features.site_settings.site_settings_core import get_installed_packages
        pkgs = get_installed_packages()
        q = request.args.get('q', '').strip().lower()
        if q:
            pkgs = [p for p in pkgs if q in p['name'].lower()]
        return {'items': pkgs, 'total': len(pkgs)}, 200


@site_settings_ns.route('/packages/update')
class PackageUpdate(Resource):
    method_decorators = [api_require_permission('admin_only')]

    def post(self):
        """Upgrade an installed package via pip."""
        data = request.get_json(silent=True) or {}
        name = data.get('name', '').strip()
        if not name:
            return {'message': 'Package name required'}, 400
        from ..features.site_settings.site_settings_core import update_package_core
        ok, output = update_package_core(name)
        if ok:
            log_action(
                f"Package updated: {name}",
                "package_update",
                category=api_category('admin'),
                level="success",
                object_type="package",
                is_public=False,
                meta={'name': name},
            )
        return {'message': output, 'ok': ok}, 200 if ok else 400


@site_settings_ns.route('/packages/install')
class PackageInstall(Resource):
    method_decorators = [api_require_permission('admin_only')]

    def post(self):
        """Install a new package via pip."""
        data = request.get_json(silent=True) or {}
        name = data.get('name', '').strip()
        if not name:
            return {'message': 'Package name required'}, 400
        from ..features.site_settings.site_settings_core import install_package_core
        ok, output = install_package_core(name)
        if ok:
            log_action(
                f"Package installed: {name}",
                "package_install",
                category=api_category('admin'),
                level="success",
                object_type="package",
                is_public=False,
                meta={'name': name},
            )
        return {'message': output, 'ok': ok}, 200 if ok else 400
