from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, jsonify)
from flask_login import current_user, login_required, login_user, logout_user

from ...core.db_class.user import User
from .form import AddNewUserForm, LoginForm, EditUserForm
from ..account import account_core as AccountCore
from ...core.utils.utils import form_to_dict

account_blueprint = Blueprint('account', __name__)


# ── Profile ───────────────────────────────────────────────────────────────────

@account_blueprint.route('/')
@login_required
def index():
    return render_template('account/profile.html', user=current_user)


# ── Edit profile ──────────────────────────────────────────────────────────────

@account_blueprint.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_user():
    form = EditUserForm()

    if form.validate_on_submit():
        form_dict = form_to_dict(form)
        user, message = AccountCore.edit_user_core(form_dict, current_user.id)
        flash(message, 'success' if user else 'danger')
        return redirect(url_for('account.index'))

    if request.method == 'GET':
        form.first_name.data     = current_user.first_name
        form.last_name.data      = current_user.last_name
        form.email.data          = current_user.email
        form.username_handle.data= current_user.username
        form.bio.data            = current_user.bio
        form.phone.data          = current_user.phone
        form.job_title.data      = current_user.job_title
        form.company.data        = current_user.company
        form.location.data       = current_user.location
        form.website.data        = current_user.website
        form.social_twitter.data = current_user.social_twitter
        form.social_github.data  = current_user.social_github
        form.social_linkedin.data= current_user.social_linkedin

    return render_template('account/edit.html', form=form)


# ── Avatar upload (JSON endpoint) ─────────────────────────────────────────────

@account_blueprint.route('/avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        return jsonify({'message': 'No file provided'}), 400
    f = request.files['avatar']
    if not f or f.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    filename, msg = AccountCore.save_avatar_core(f, current_user.id)
    if filename:
        return jsonify({'message': msg, 'filename': filename}), 200
    return jsonify({'message': msg}), 400


@account_blueprint.route('/avatar', methods=['DELETE'])
@login_required
def delete_avatar():
    ok, msg = AccountCore.delete_avatar_core(current_user.id)
    return jsonify({'message': msg}), 200 if ok else 400


# ── Reload API key (JSON endpoint) ────────────────────────────────────────────

@account_blueprint.route('/reload-api-key', methods=['POST'])
@login_required
def reload_api_key():
    user, msg = AccountCore.reload_api_key_core(current_user.id)
    if user:
        return jsonify({'message': msg, 'api_key': user.api_key}), 200
    return jsonify({'message': msg}), 400


# ── Create user ───────────────────────────────────────────────────────────────

@account_blueprint.route('/register', methods=['GET', 'POST'])
def create_user():
    form = AddNewUserForm()
    if form.validate_on_submit():
        form_dict = form_to_dict(form)
        if not current_user.is_authenticated or not current_user.is_admin():
            form_dict['role_id'] = 3   # read-only for self-registration
        user, message = AccountCore.create_user_core(form_dict)
        flash(message, 'success' if user else 'danger')
        if user:
            return redirect(url_for('account.index'))
    return render_template('account/create.html', form=form)


# ── Auth ──────────────────────────────────────────────────────────────────────

@account_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # public
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password_hash and user.verify_password(form.password.data):
            if not user.is_verified:
                flash('Your account is pending verification. Please wait for admin approval.', 'warning')
            else:
                # Reset force_logout so a previously disconnected user can re-authenticate
                if user.force_logout:
                    from ... import db as _db
                    user.force_logout = False
                    _db.session.commit()
                login_user(user, form.remember_me.data)
                return redirect(request.args.get('next') or url_for('home.home'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('account/login.html', form=form)


@account_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('account.login'))
