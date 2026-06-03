from datetime import datetime
from ... import db, login_manager
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin, AnonymousUserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    # ── Core identity ────────────────────────────────────────
    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name    = db.Column(db.String(64), index=True)
    last_name     = db.Column(db.String(64), index=True)
    email         = db.Column(db.String(128), unique=True, index=True)
    username      = db.Column(db.String(32),  unique=True, nullable=True, index=True)
    role_id       = db.Column(db.Integer, index=True)
    password_hash = db.Column(db.String(256))
    api_key       = db.Column(db.String(60), index=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Profile ──────────────────────────────────────────────
    bio             = db.Column(db.String(500), nullable=True)
    avatar_filename = db.Column(db.String(255), nullable=True)
    phone           = db.Column(db.String(25),  nullable=True)
    job_title       = db.Column(db.String(100), nullable=True)
    company         = db.Column(db.String(100), nullable=True)
    location        = db.Column(db.String(100), nullable=True)

    # ── Social / links ───────────────────────────────────────
    website         = db.Column(db.String(200), nullable=True)
    social_twitter  = db.Column(db.String(50),  nullable=True)
    social_github   = db.Column(db.String(50),  nullable=True)
    social_linkedin = db.Column(db.String(200), nullable=True)

    # ── Role helpers ─────────────────────────────────────────
    def is_admin(self):
        r = Role.query.get(self.role_id)
        return bool(r and r.admin)

    def read_only(self):
        r = Role.query.get(self.role_id)
        return bool(r and r.read_only)

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def display_name(self):
        return self.username or f"{self.first_name} {self.last_name}"

    def initials(self):
        f = (self.first_name or ' ')[0].upper()
        l = (self.last_name  or ' ')[0].upper()
        return f + l

    # ── Password ─────────────────────────────────────────────
    @property
    def password(self):
        raise AttributeError('`password` is not readable')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # ── Serialisation ────────────────────────────────────────
    def to_json(self):
        return {
            'id':             self.id,
            'first_name':     self.first_name,
            'last_name':      self.last_name,
            'email':          self.email,
            'username_handle': self.username,
            'role_id':        self.role_id,
            'bio':            self.bio,
            'phone':          self.phone,
            'job_title':      self.job_title,
            'company':        self.company,
            'location':       self.location,
            'website':        self.website,
            'social_twitter': self.social_twitter,
            'social_github':  self.social_github,
            'social_linkedin':self.social_linkedin,
            'created_at':     self.created_at.isoformat() if self.created_at else None,
            'has_avatar':     bool(self.avatar_filename),
        }


class AnonymousUser(AnonymousUserMixin):
    def is_admin(self):   return False
    def read_only(self):  return True
    def initials(self):   return '?'


login_manager.anonymous_user = AnonymousUser


class Role(db.Model):
    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name        = db.Column(db.String(64), index=True, unique=True)
    description = db.Column(db.String, nullable=True)
    admin       = db.Column(db.Boolean, default=False)
    read_only   = db.Column(db.Boolean, default=False)

    def to_json(self):
        return {
            'id':          self.id,
            'name':        self.name,
            'description': self.description,
            'admin':       self.admin,
            'read_only':   self.read_only,
        }
