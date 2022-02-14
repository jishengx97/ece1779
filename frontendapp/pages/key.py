import requests
from flask import render_template, url_for, request
from frontendapp import webapp
from flask import json


@webapp.route('/key',methods=['GET'])
def key_form():
    return render_template("pages/key/key_form.html", title = "KEY", error_msg = None, img = None)

@webapp.route('/key',methods=['POST'])
def key_save():
    error_msg = None

    key_input = request.form.get("key_input")
    if key_input == "":
        error_msg = "Missing key"
        return render_template("pages/key/key_form.html",title = "KEY",error_msg = error_msg, img = None)

    r = requests.post("http://127.0.0.1:5001/get", data={'key':key_input})

    if r.status_code == 200:
        error_msg = "KEY SUCCESS"
        img = r.json()
    else:
        error_msg = r.json()
        img = None

    return render_template("pages/key/key_form.html", title = "KEY", error_msg = error_msg, img = img)