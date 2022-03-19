from flask import render_template, url_for, request
from frontendapp import webapp, ip_list
from flask import json
from common import models
import hashlib

@webapp.route('/memcaches/launched',methods=['POST'])
def memcaches_launched():
    ip_input = request.form.get("ip_input")
    ip_list.add(ip_input)
    data = {"success": "true"}
    response = webapp.response_class(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )
    return response

@webapp.route('/memcaches/terminated',methods=['POST'])
def memcaches_terminated():
    ip_input = request.form.get("ip_input")
    if ip_input in ip_list:
        ip_list.remove(ip_input)
        data = {"success": "true"}
        response = webapp.response_class(
                response=json.dumps(data),
                status=200,
                mimetype='application/json'
            )
        return response
    data = {"error": {"code" : "400", "message":"IP address is not known yet."},
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