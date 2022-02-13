from flask import Flask

webapp = Flask(__name__)

from frontendapp import main
from frontendapp.pages import upload
from frontendapp.pages import key
from frontendapp.pages import list_keys
