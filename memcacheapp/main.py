
from flask import render_template, url_for, request
from memcacheapp import webapp, memcache,capacity,policy
from flask import json
import random
import base64

@webapp.route('/')
def main():
    return render_template("main.html")

@webapp.route('/get',methods=['POST'])
def get():
    key = request.form.get('key')

    if key in memcache:
        memcache.move_to_end(key)
        # value = memcache[key]
        value = base64.b64encode(memcache[key]).decode('utf-8')
        response = webapp.response_class(
            response=json.dumps(value),
            status=200,
            mimetype='application/json'
        )
    else:
        response = webapp.response_class(
            response=json.dumps("Unknown key"),
            status=400,
            mimetype='application/json'
        )

    return response

@webapp.route('/put',methods=['POST'])
def put():
    key = request.form.get('key')
    value = request.files['image'].getvalue()

    if key in memcache:
        #update entry
        memcache.move_to_end(key)
        memcache[key] = value
    else:
        # insert new entry
        if len(memcache) >= capacity:
            ##replace
            if policy == 'LRU':
                memcache.popitem(last = False) 
            else:
                removekey = random.choice(list(memcache.keys()))
                memcache.pop(removekey)
            memcache[key] = value
        else:
            memcache[key] = value
            

    response = webapp.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )

    return response

@webapp.route('/clear',methods=['POST'])
def clear():
    # memcache[key] = value
    # for key, value in memcache.items():
    memcache.clear()        
    response = webapp.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )

    return response

@webapp.route('/drop',methods=['POST'])
def drop():
    key = request.form.get('key')

    if key in memcache:
        value = memcache[key]
        memcache.pop(key)
        response = webapp.response_class(
            response=json.dumps("OK"),
            status=200,
            mimetype='application/json'
        )
    else:
        response = webapp.response_class(
            response=json.dumps("Unknown key"),
            status=400,
            mimetype='application/json'
        )

    return response

# function to debug
@webapp.route('/listall',methods=['POST'])
def listall():
    files = []
    for key in memcache.keys():
        files.append(base64.b64encode(memcache[key]).decode('utf-8'))
        # filee = json.dumps(memcache[key].decode("utf-8"))
    return render_template("image.html", user_image = files)
