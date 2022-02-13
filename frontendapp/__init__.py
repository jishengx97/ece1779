from flask import Flask

webapp = Flask(__name__)

from frontendapp import main
from frontendapp.api import upload
from frontendapp.api import key
from frontendapp.api import list_keys
