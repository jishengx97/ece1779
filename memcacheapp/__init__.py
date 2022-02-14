from flask import Flask
from collections import OrderedDict
global memcache

webapp = Flask(__name__)
memcache = OrderedDict()
capacity  =  5
policy = 'LRU'
from memcacheapp import main




