
from flask import render_template, url_for, request
from frontendapp import webapp
from flask import json
from common import models


@webapp.route('/',methods=['GET'], strict_slashes=False)
def main():
    return render_template("main.html",title = "MAIN")

@webapp.after_request
def disable_cache(response):
    response.cache_control.max_age = 0
    response.cache_control.public = True
    return response