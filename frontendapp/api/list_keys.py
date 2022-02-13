from flask import render_template, url_for, request
from frontendapp import webapp
from flask import json


@webapp.route('/api/list_keys',methods=['GET'])
def list_keys_form():
    return render_template("api/list_keys/list_keys_form.html",title = "LIST_KEYS")