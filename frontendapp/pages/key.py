import requests
from flask import render_template, url_for, request, send_from_directory
from frontendapp import webapp
from flask import json
from common import models
import os
@webapp.route('/key',methods=['GET'])
def key_form():
    return render_template("pages/key/key_form.html", title = "KEY", error_msg = None, img = None, img_file = None)

@webapp.route('/key',methods=['POST'])
def key_save():
    error_msg = None

    key_input = request.form.get("key_input")
    if key_input == "":
        error_msg = "Missing key"
        return render_template("pages/key/key_form.html",title = "KEY",error_msg = error_msg, img = None, img_file = None)

    r = requests.post("http://127.0.0.1:5001/get", data={'key':key_input})

    img = None
    img_file = None
    if r.status_code == 200:
        error_msg = "FROM CACHE"
        img = r.json()
    else:
        error_msg = "FROM LOCAL"
        local_session = webapp.db_session()
        result = local_session.query(models.KeyAndFileLocation).filter(models.KeyAndFileLocation.key == key_input)
        if result.count() == 0:
            error_msg = "KEY DID NOT EXIST"
            return render_template("pages/key/key_form.html", title = "KEY", error_msg = error_msg, img = img, img_file = img_file)
        img_file_path, img_file = os.path.split(result.first().file_location)
        r = requests.post("http://127.0.0.1:5001/put", data={'key':key_input}, files={'image':open(result.first().file_location,'rb')})
        if r.status_code != 200:
            error_msg = r.json()
    return render_template("pages/key/key_form.html", title = "KEY", error_msg = error_msg, img = img, img_file = img_file)

@webapp.route('/key/<filename>')
def send_img(filename):
    return send_from_directory("/home/ubuntu/ece1779/images/",filename)