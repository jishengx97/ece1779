from flask import Flask, _app_ctx_stack
from sqlalchemy.orm import scoped_session
from common import database
from decouple import config

webapp = Flask(__name__)
webapp.url_map.strict_slashes = False

from managerapp import main