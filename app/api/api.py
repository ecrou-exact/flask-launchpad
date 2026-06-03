import os
from flask import Blueprint
from flask_restx import Api

api_blueprint = Blueprint(
    "api", __name__, url_prefix="/api"
)

authorizations = {
    "apikey": {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-KEY",
    }
}

def version():
    with open(os.path.join(os.getcwd(),"version")) as read_version:
        loc = read_version.readlines()
    return loc[0].rstrip()


api = Api(api_blueprint,
    title='flask-launchpad API', 
    description="<a href='https://github.com/ecrou-exact/flask-launchpad' rel='noreferrer' target='_blank'>"
    "<img src='/static/image/logo.png'  /></a><br />"
    'API to query flask-launchpad.',
    version=version(), 
    # license="GNU Affero General Public License version 3",
    # license_url="https://www.gnu.org/licenses/agpl-3.0.html",
    doc='/',
    security="apikey",
    authorizations=authorizations
)

from .account_api import account_ns
from .config_api import config_ns
from .admin_api import admin_ns
from .log_api import log_ns

api.add_namespace(account_ns, path="/account")
api.add_namespace(config_ns, path="/config")
api.add_namespace(admin_ns, path="/admin")
api.add_namespace(log_ns, path="/log")




