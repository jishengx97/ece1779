from flask import Flask
from sqlalchemy.orm import scoped_session
from common import database

webapp = Flask(__name__)

database.init_db()

webapp.db_session = scoped_session(database.SessionLocal)

# initialzes the database and populates them with default values if necessary
from frontendapp import initialize_db
initialize_db.set_db_default_values()

from frontendapp import main
from frontendapp.pages import upload
from frontendapp.pages import key
from frontendapp.pages import list_keys
