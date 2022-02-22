import requests
from flask import render_template, url_for, request, send_from_directory
from frontendapp import webapp
from flask import json
from common import models
import os
import base64
key_title = "Get Image From Memcache Using Key"

@webapp.route('/key',methods=['GET'])
def key_form():
    return render_template("pages/key/key_form.html", title = key_title, error_msg = None, img = None, img_file = None)

@webapp.route('/key',methods=['POST'])
def key_save():
    error_msg = None

    key_input = request.form.get("key_input")
    if key_input == "":
        error_msg = "Missing key"
        return render_template("pages/key/key_form.html",title = key_title,error_msg = error_msg, img = None, img_file = None)

    r = requests.post("http://127.0.0.1:5001/get", data={'key':key_input})

    img = None
    img_file = None
    if r.status_code == 200:
        error_msg = "Got the image from memcache directly!"
        img = r.json()
    else:
        error_msg = "Key put to memcache!"
        local_session = webapp.db_session()
        result = local_session.query(models.KeyAndFileLocation).filter(models.KeyAndFileLocation.key == key_input)
        if result.count() == 0:
            error_msg = "Key does not exist!"
            return render_template("pages/key/key_form.html", title = key_title, error_msg = error_msg, img = img, img_file = img_file)
        # img_file_path, img_file = os.path.split(result.first().file_location)
        img_binary1 = open(result.first().file_location,'rb')
        img_binary2 = open(result.first().file_location,'rb')
        img_file = base64.b64encode(img_binary2.read()).decode()
        r = requests.post("http://127.0.0.1:5001/put", data={'key':key_input}, files={'image':img_binary1})
        img_binary1.close()
        img_binary2.close()
        if r.status_code != 200:
            error_msg = r.json()
    return render_template("pages/key/key_form.html", title = key_title, error_msg = error_msg, img = img, img_file = img_file)

@webapp.route('/api/key/<key_value>',methods=['POST'])
def test_key(key_value):
    r = requests.post("http://127.0.0.1:5001/get", data={'key':key_value})

    img = None
    img_file = None
    if r.status_code == 200:
        error_msg = "Got the image from memcache directly!"
        img = r.json()
    else:
        error_msg = "Key put to memcache!"
        local_session = webapp.db_session()
        result = local_session.query(models.KeyAndFileLocation).filter(models.KeyAndFileLocation.key == key_value)
        if result.count() == 0:
            error_msg = "Key does not exist!"
            data = {"error": {"code" : "400", "message":"key does not exist."},
                    "success":"false"}
            response = webapp.response_class(
                response=json.dumps(data),
                status=400,
                mimetype='application/json'
            )
            return response
        # img_file_path, img_file = os.path.split(result.first().file_location)
        img_binary1 = open(result.first().file_location,'rb')
        img_binary2 = open(result.first().file_location,'rb')
        img = base64.b64encode(img_binary2.read()).decode()
        r = requests.post("http://127.0.0.1:5001/put", data={'key':key_value}, files={'image':img_binary1})
        img_binary1.close()
        img_binary2.close()
        if r.status_code != 200:
            data = {"error": {"code" : "400", "message":"image size is larger than cache capacity."},
                    "success":"false"}
            response = webapp.response_class(
                response=json.dumps(data),
                status=400,
                mimetype='application/json'
            )
            return response
    data = {"success":"true",
            "content":img}
    response = webapp.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    return response