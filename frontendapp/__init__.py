from flask import Flask

webapp = Flask(__name__)

from frontendapp import main
from frontendapp import upload
from frontendapp import get

