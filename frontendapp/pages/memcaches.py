from flask import render_template, url_for, request
from frontendapp import webapp, ip_list
from flask import json
from common import models
import hashlib
import json

@webapp.route('/memcaches/launched',methods=['POST'])
def memcaches_launched():
    list_string = request.form.get("list_string")
    temp_list = json.loads(list_string)
    global ip_list
    ip_list = ip_list + temp_list
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
    global ip_list
    if terminate_num <= len(ip_list):
        ip_list = ip_list[:-terminate_num]
        data = {"success": "true"}
        response = webapp.response_class(
                response=json.dumps(data),
                status=200,
                mimetype='application/json'
            )
        return response
    data = {"error": {"code" : "400", "message":"terminate_num > len(ip_list)"},
            "success":"false"}
    response = webapp.response_class(
        response=json.dumps(data),
        status=400,
        mimetype='application/json'
    )
    return response

@webapp.route('/memcaches/hash',methods=['POST'])
def key_hash_int():
    key_input = request.form.get("key_input")
    hashvalue = hashlib.md5(key_input.encode())
    hexvalue = hashvalue.hexdigest()
    result = int(hexvalue,16)
    num_cycle = result%16
    data = {"success": "true","hashvalue": num_cycle}
    response = webapp.response_class(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )
    return response
