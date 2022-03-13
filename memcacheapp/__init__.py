from flask import Flask, _app_ctx_stack
from sqlalchemy.orm import scoped_session
from common import database, models
from collections import OrderedDict
from apscheduler.schedulers.background import BackgroundScheduler
from multiprocessing import Lock
import atexit
global memcache

webapp = Flask(__name__)

database.init_db()

webapp.db_session = scoped_session(database.SessionLocal, scopefunc=_app_ctx_stack.__ident_func__)

# initialzes the database and populates them with default values if necessary
from memcacheapp import initialize_db
initialize_db.set_db_default_values()

local_session = webapp.db_session()
config_result = local_session.query(models.MemcacheConfig).first()
memcache = OrderedDict()
capacity  =  config_result.capacity_in_mb 
policy = config_result.replacement_policy
current_size = 0
num_item = 0
num_request = 0
num_miss = 0
num_access = 0
lock = Lock()
from memcacheapp import main

scheduler = BackgroundScheduler(timezone='US/Eastern')
scheduler.add_job(func=main.print_cache_stats, trigger="interval", seconds=5)
# scheduler.start()
bg_scheduler_started = True


atexit.register(lambda: scheduler.shutdown())