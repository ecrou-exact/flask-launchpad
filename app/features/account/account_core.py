from app.core.utils.utils import generate_api_key

from ... import db
from ...core.db_class.user import User, Role

def get_all_roles():
    """Return all roles"""
    return Role.query.all()

def get_user(id):
    """Return the user"""
    return User.query.get(id)


def edit_user_core(form_dict, id) -> tuple[User, str]:
    """Edit the user to the DB"""
    try:
        user = get_user(id)

        user.first_name=form_dict["first_name"]
        user.last_name=form_dict["last_name"]
        user.email=form_dict["email"]
        if form_dict.get("password"):  
            user.password = form_dict["password"] 

        db.session.commit()
        return user, "User updated successfully"
    except Exception as e:
        return None, f"Error updating user"


def create_user_core(form_dict) -> tuple:
    """Create the user to the DB"""
    try:
        user = User(
            first_name=form_dict["first_name"],
            last_name=form_dict["last_name"],
            email=form_dict["email"],
            password=form_dict["password"],
            role_id=form_dict["role_id"],
            api_key=generate_api_key()
        )
        db.session.add(user)
        db.session.commit()
        from ...core.db_class.config import UserConfig
        config = UserConfig(user_id=user.id, created_by=user.id)
        db.session.add(config)
        db.session.commit()
        return user, "User created successfully"
    except Exception:
        db.session.rollback()
        return None, "Error creating user"