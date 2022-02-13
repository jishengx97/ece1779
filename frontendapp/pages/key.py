from flask import render_template, url_for, request
from frontendapp import webapp
from flask import json


@webapp.route('/key',methods=['GET'])
def key_form():
    return render_template("pages/key/key_form.html",title = "KEY")