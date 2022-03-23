import requests
from flask import render_template, url_for, request, send_from_directory
from frontendapp import webapp, s3_bucket_name, lock_S3, lock_RDS
from flask import json
from common import models
import os
import io
import base64
import boto3
from decouple import config
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
    
    img = None
    img_file = None    
    r = requests.post("http://127.0.0.1:5000/memcaches/hash", data={'key_input':key_input})
    r_dict = r.json()
    ip_address = r_dict['ip_address']

    if ip_address == '':
        error_msg = "No memcaches yet! From S3 KEY=" + key_input
        lock_RDS.acquire()
        lock_S3.acquire()
        local_session = webapp.db_session()
        client = boto3.client('s3',aws_access_key_id=config('AWSAccessKeyId'), aws_secret_access_key=config('AWSSecretKey'))
        result = local_session.query(models.KeyAndFileLocation).filter(models.KeyAndFileLocation.key == key_input)
        if result.count() == 0:
            error_msg = error_msg + " ,Key does not exist!"
            return render_template("pages/key/key_form.html", title = key_title, error_msg = error_msg, img = img, img_file = img_file)
        obj = client.get_object(Bucket=s3_bucket_name, Key=result.first().file_location)
        lock_RDS.release()
        lock_S3.release()
        file_like_obj = io.BytesIO(obj['Body'].read())
        img_file = base64.b64encode(file_like_obj.read()).decode()
        return render_template("pages/key/key_form.html", title = key_title, error_msg = error_msg, img = img, img_file = img_file)

    ip_id = r_dict['ip_id']
    r = requests.post("http://" + ip_address + "/get", data={'key':key_input})

    if r.status_code == 200:
        error_msg = "Got the image from memcache" +ip_id+ " directly! KEY=" + key_input
        img = r.json()
    else:
        error_msg = "Key put to memcache" +ip_id+ " From S3! KEY=" + key_input
        lock_RDS.acquire()
        lock_S3.acquire()
        local_session = webapp.db_session()
        client = boto3.client('s3',aws_access_key_id=config('AWSAccessKeyId'), aws_secret_access_key=config('AWSSecretKey'))
        result = local_session.query(models.KeyAndFileLocation).filter(models.KeyAndFileLocation.key == key_input)
        if result.count() == 0:
            error_msg = error_msg + " ,Key does not exist!"
            return render_template("pages/key/key_form.html", title = key_title, error_msg = error_msg, img = img, img_file = img_file)
        # img_file_path, img_file = os.path.split(result.first().file_location)

        obj = client.get_object(Bucket=s3_bucket_name, Key=result.first().file_location)
        lock_RDS.release()
        lock_S3.release()
        file_like_obj = io.BytesIO(obj['Body'].read())

        # img_binary1 = open(result.first().file_location,'rb')
        # img_binary2 = open(result.first().file_location,'rb')
        img_file = base64.b64encode(file_like_obj.read()).decode()
        file_like_obj.seek(0)
        r = requests.post("http://" + ip_address + "/put", data={'key':key_input}, files={'image':file_like_obj})
        # img_binary1.close()
        # img_binary2.close()

        if r.status_code != 200:
            error_msg = error_msg + r.json()
    return render_template("pages/key/key_form.html", title = key_title, error_msg = error_msg, img = img, img_file = img_file)

@webapp.route('/api/key/<key_value>',methods=['POST'])
def test_key(key_value):
    key_input = key_value
    img = None
    img_file = None
    r = requests.post("http://127.0.0.1:5000/memcaches/hash", data={'key_input':key_input})
    r_dict = r.json()
    ip_address = r_dict['ip_address']
    if ip_address != '':
        r = requests.post("http://" + ip_address + "/get", data={'key':key_input})
        if r.status_code == 200:
            error_msg = "Got the image from memcache directly!"
            img = r.json()
    if img == None:
        lock_RDS.acquire()
        lock_S3.acquire()
        local_session = webapp.db_session()
        client = boto3.client('s3',aws_access_key_id=config('AWSAccessKeyId'), aws_secret_access_key=config('AWSSecretKey'))
        result = local_session.query(models.KeyAndFileLocation).filter(models.KeyAndFileLocation.key == key_input)
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
        obj = client.get_object(Bucket=s3_bucket_name, Key=result.first().file_location)
        lock_RDS.release()
        lock_S3.release()
        file_like_obj = io.BytesIO(obj['Body'].read())
        img = base64.b64encode(file_like_obj.read()).decode()
        file_like_obj.seek(0)
        if ip_address != '':
            r = requests.post("http://" + ip_address + "/put", data={'key':key_input}, files={'image':file_like_obj})
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
