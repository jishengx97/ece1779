from flask import render_template, url_for, request
from frontendapp import webapp, lock_S3, lock_RDS, s3_bucket_name
from flask import json
from common import models
import hashlib
import json
import requests
from decouple import config
from multiprocessing import Lock
import boto3
lock = Lock()
ip_list = []

@webapp.route('/memcaches/launched',methods=['POST'])
def memcaches_launched():
    list_string = request.form.get("list_string")
    temp_list = json.loads(list_string)
    lock.acquire()
    global ip_list
    ip_list = ip_list + temp_list
    lock.release()
    data = {"success": "true"}
    response = webapp.response_class(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )
    return response

@webapp.route('/memcaches/terminated',methods=['POST'])
def memcaches_terminated():
    terminate_num = int(request.form.get("terminate_num"))
    lock.acquire()
    global ip_list
    if terminate_num <= len(ip_list):
        ip_list = ip_list[:-terminate_num]
        lock.release()
        data = {"success": "true"}
        response = webapp.response_class(
                response=json.dumps(data),
                status=200,
                mimetype='application/json'
            )
        return response
    lock.release()
    data = {"error": {"code" : "400", "message":"terminate_num > len(ip_list)"},
            "success":"false"}
    response = webapp.response_class(
        response=json.dumps(data),
        status=400,
        mimetype='application/json'
    )
    return response

@webapp.route('/memcaches/hash',methods=['POST'])
def key_hash_int_ip():
    key_input = request.form.get("key_input")
    hashvalue = hashlib.md5(key_input.encode())
    hexvalue = hashvalue.hexdigest()
    result = int(hexvalue,16)
    num_cycle = result%16
    ip_address = ""
    lock.acquire()
    global ip_list
    if len(ip_list) < 1:
        lock.release()
        data = {"ip_address": ip_address}
        response = webapp.response_class(
                response=json.dumps(data),
                status=200,
                mimetype='application/json'
            )
        return response
    else:
        ip_id = num_cycle%len(ip_list)
        ip_address = ip_list[ip_id]
        lock.release()
        data = {"ip_address": ip_address, "ip_id": str(ip_id)}
        response = webapp.response_class(
                response=json.dumps(data),
                status=200,
                mimetype='application/json'
            )
        return response

@webapp.route('/memcaches/invalidateKey',methods=['POST'])
def memcaches_invalidateKey():
    key = request.form.get('key')
    lock.acquire()
    global ip_list
    for ip_address in ip_list:
        try:
            requests.post("http://" + ip_address + "/invalidateKey", data={'key':key,}, timeout=0.5)
        except requests.Timeout:
            pass
    lock.release()        
    response = webapp.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )
    return response

@webapp.route('/memcaches/delete_all_image',methods=['POST'])
def memcaches_delete_all_image():
    lock.acquire()
    lock_RDS.acquire()
    lock_S3.acquire()

    s3 = boto3.resource('s3',aws_access_key_id=config('AWSAccessKeyId'), aws_secret_access_key=config('AWSSecretKey'))
    bucket = s3.Bucket(s3_bucket_name)
    bucket.objects.all().delete()

    local_session = webapp.db_session() 
    result_count = local_session.query(models.KeyAndFileLocation).delete() 
    local_session.commit()

    global ip_list
    for ip_address in ip_list:
        try:
            requests.post("http://" + ip_address + "/clear", timeout=0.5)
        except requests.Timeout:
            pass
    lock.release() 
    lock_RDS.release() 
    lock_S3.release()     
    response = webapp.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )
    return response