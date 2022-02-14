from flask import Flask
from sqlalchemy.orm import scoped_session
from common import database
from collections import OrderedDict
global memcache

webapp = Flask(__name__)

database.init_db()

webapp.db_session = scoped_session(database.SessionLocal)

# initialzes the database and populates them with default values if necessary
from memcacheapp import initialize_db
initialize_db.set_db_default_values()

memcache = OrderedDict()
capacity  =  2
policy = 'LRU'
current_size = 0
num_item = 0
num_request = 0
num_miss = 0
num_access = 0
from memcacheapp import main




