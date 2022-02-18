from flask import Flask
from sqlalchemy.orm import scoped_session
from common import database
from collections import OrderedDict
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
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

scheduler = BackgroundScheduler(timezone='US/Eastern')
scheduler.add_job(func=main.print_cache_stats, trigger="interval", seconds=5)
scheduler.start()
bg_scheduler_started = True

atexit.register(lambda: scheduler.shutdown())