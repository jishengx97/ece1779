from flask import Flask
from sqlalchemy.orm import scoped_session
from common import database
from collections import OrderedDict
global memcache

webapp = Flask(__name__)

database.init_db()

webapp.db_session = scoped_session(database.SessionLocal)

memcache = OrderedDict()
capacity  =  5
policy = 'LRU'
from memcacheapp import main




