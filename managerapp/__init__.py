from flask import Flask, _app_ctx_stack
from sqlalchemy.orm import scoped_session
# from common import database
from decouple import config
import multiprocessing
# manager = multiprocessing.Manager()
# instance_pool = manager.list()
instance_pool = []
webapp = Flask(__name__)
webapp.url_map.strict_slashes = False
current_pool_size = [1]
pending_instance = 0
frontend_id = ''
memcache_id = ''
from managerapp import main
from managerapp.pages import pool_stats, manual_config


