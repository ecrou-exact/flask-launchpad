from flask import request
from flask_login import current_user
from ... import db
from ...core.db_class.config import UserConfig, THEME_CHOICES, NAV_POSITION_CHOICES, TOAST_POSITION_CHOICES, TOAST_STYLE_CHOICES, TOAST_DURATION_MIN, TOAST_DURATION_MAX


def _resolve_user_id():
    """Return the authenticated user's id from session OR API key."""
    if current_user.is_authenticated:
        return current_user.id
    api_key = request.headers.get('X-API-KEY')
    if api_key:
        from ...core.utils.utils import get_user_api
        user = get_user_api(api_key)
        if user:
            return user.id
    return None


def get_user_config(user_id=None):
    uid = user_id or _resolve_user_id()
    if not uid:
        return None
    return UserConfig.query.filter_by(user_id=uid, is_active=True).first()


def create_default_config_core(user_id) -> tuple:
    try:
        existing = UserConfig.query.filter_by(user_id=user_id).first()
        if existing:
            return existing, "Config already exists"
        config = UserConfig(user_id=user_id, created_by=user_id)
        db.session.add(config)
        db.session.commit()
        return config, "Config created"
    except Exception:
        db.session.rollback()
        return None, "Error creating config"


def update_config_core(form_dict) -> tuple:
    try:
        uid = _resolve_user_id()
        config = get_user_config(uid)
        if not config:
            config, msg = create_default_config_core(uid)
            if not config:
                return None, msg

        if 'theme' in form_dict:
            if form_dict['theme'] not in THEME_CHOICES:
                return None, "Invalid theme"
            config.theme = form_dict['theme']

        if 'nav_position' in form_dict:
            if form_dict['nav_position'] not in NAV_POSITION_CHOICES:
                return None, "Invalid nav position"
            config.nav_position = form_dict['nav_position']

        if 'sidebar_collapsed' in form_dict:
            config.sidebar_collapsed = bool(form_dict['sidebar_collapsed'])

        if 'toast_position' in form_dict:
            if form_dict['toast_position'] not in TOAST_POSITION_CHOICES:
                return None, "Invalid toast position"
            config.toast_position = form_dict['toast_position']

        if 'toast_style' in form_dict:
            if form_dict['toast_style'] not in TOAST_STYLE_CHOICES:
                return None, "Invalid toast style"
            config.toast_style = form_dict['toast_style']

        if 'toast_duration' in form_dict:
            val = int(form_dict['toast_duration'])
            if not (TOAST_DURATION_MIN <= val <= TOAST_DURATION_MAX):
                return None, f"Duration must be between {TOAST_DURATION_MIN} and {TOAST_DURATION_MAX}"
            config.toast_duration = val

        db.session.commit()
        return config, "Settings saved"
    except Exception:
        db.session.rollback()
        return None, "Error saving settings"
