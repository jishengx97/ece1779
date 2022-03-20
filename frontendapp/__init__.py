from flask import Flask, _app_ctx_stack
from sqlalchemy.orm import scoped_session
from common import database
from decouple import config

webapp = Flask(__name__)
webapp.url_map.strict_slashes = False

database.init_db()

webapp.db_session = scoped_session(database.SessionLocal, scopefunc=_app_ctx_stack.__ident_func__)
s3_bucket_name = config('AWS_STORAGE_BUCKET_NAME')

# initialzes the database and populates them with default values if necessary
from frontendapp import initialize_db
initialize_db.set_db_default_values()

from frontendapp import main
from frontendapp.pages import upload, key, list_keys, config, show_stats, memcaches
