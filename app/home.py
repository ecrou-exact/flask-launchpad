from flask import Blueprint, render_template
from flask import session

home_blueprint = Blueprint(
    'home',
    __name__,
    template_folder='templates',
    static_folder='static'
)

@home_blueprint.route("/")
def home():
    return render_template("home.html")

