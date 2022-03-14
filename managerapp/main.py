
from flask import render_template, url_for, request
from managerapp import webapp
from flask import json


@webapp.route('/',methods=['GET'], strict_slashes=False)
def main():
    return render_template("main.html",title = "Welcome to cache manager")

@webapp.after_request
def disable_cache(response):
    response.cache_control.max_age = 0
    response.cache_control.public = True
    return response

#@webapp.teardown_appcontext
#def teardown_db(exception=None):
#    webapp.db_session.remove()
