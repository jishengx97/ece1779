
from flask import render_template, url_for, request
from memcacheapp import webapp, memcache,capacity,policy,current_size,num_item,num_request,num_miss,num_access
from flask import json
from common import models
import random
import base64
import sys
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from pytz import timezone

def print_cache_stats():
    msg = ''
    msg += "Capacity: " + str(capacity) + " MB" + ".    "
    msg += "current_size: " + str(current_size) + " bytes"+ ".  "
    msg += "policy: " + policy + ".     "
    msg += "num_item: " + str(num_item) + ".    "
    msg += "num_request: " + str(num_request) + ".      "
    msg += "num_miss: " + str(num_miss) + ".    "
    msg += "num_access: " + str(num_access) + ".    "

    # Miss rate and hit rate in percentage
    if num_request > 0:
        miss_rate = num_miss / num_request * 100
        hit_rate = (num_request - num_miss) / num_request * 100
    else:
        miss_rate = 0.0
        hit_rate = 0.0
    msg += "miss rate: " + str(miss_rate) + "%.    "
    msg += "hit rate: " + str(hit_rate) + "%.    "

    eastern = timezone('US/Eastern')
    current_time = datetime.now(eastern)
    msg += "curent time: " + current_time.strftime("%X") + ".    "
    print(msg)

    new_entry = models.MemcacheStats(
        num_items = num_item,
        total_size = current_size,
        num_requests_served = num_request,
        miss_rate = miss_rate,
        hit_rate = hit_rate,
        stats_timestamp = current_time
    )
    webapp.db_session.add(new_entry)
    webapp.db_session.commit()

@webapp.route('/')
def main():

    return render_template("main.html")

@webapp.route('/get',methods=['POST'])
def get():
    global num_request
    global num_access
    global num_miss

    key = request.form.get('key')
    num_request += 1
    num_access += 1
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
        num_miss += 1
        response = webapp.response_class(
            response=json.dumps("Unknown key"),
            status=400,
            mimetype='application/json'
        )

    return response

@webapp.route('/put',methods=['POST'])
def put():
    global num_request
    # global num_access
    # global num_miss
    global num_item
    global current_size

    key = request.form.get('key')
    value = request.files['image'].getvalue()
    new_size = sys.getsizeof(value)
    num_request += 1
    # if image is larger than capacity
    if new_size > capacity * 1024 * 1024:
        response = webapp.response_class(
            response=json.dumps("image is larger than cache capacity."),
            status=400,
            mimetype='application/json'
        )

        return response
    
    # num_access += 1
    if key in memcache:
        #update entry
        
        old_size = sys.getsizeof(memcache[key])
        
        if current_size - old_size + new_size > capacity * 1024 * 1024:
            # new image is larger than old image and need to eject more image more space to save new image
            # need replacement
            #delete current key's value first
            memcache.pop(key)
            current_size -= old_size
            while current_size + new_size > capacity * 1024 * 1024:
                if policy == 'LRU':
                    least_recent_entry = memcache.popitem(last = False) 
                    current_size -= sys.getsizeof(least_recent_entry[1])
                    num_item -= 1
                else:
                    removekey = random.choice(list(memcache.keys()))
                    current_size -= sys.getsizeof(memcache[removekey])
                    memcache.pop(removekey)
                    num_item -= 1
            #insert new image
            memcache[key] = value
            current_size = current_size + new_size
        else:
            # safe to update value
            memcache.move_to_end(key)
            memcache[key] = value
            current_size = current_size - old_size + new_size
    else: #insert new key
        # num_miss += 1
        if current_size + new_size > capacity * 1024 * 1024:
            ##replace
            while current_size + new_size > capacity * 1024 * 1024:
                if policy == 'LRU':
                    least_recent_entry = memcache.popitem(last = False) 
                    current_size -= sys.getsizeof(least_recent_entry[1])
                    num_item -= 1
                else:
                    removekey = random.choice(list(memcache.keys()))
                    current_size -= sys.getsizeof(memcache[removekey])
                    memcache.pop(removekey)
                    num_item -= 1
            memcache[key] = value
            num_item += 1
            current_size += new_size
        else:
            # insert 
            memcache[key] = value
            current_size += new_size
            num_item += 1
            

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
    global num_request
    global current_size
    global num_item

    num_request += 1
    memcache.clear()     
    current_size = 0   
    num_item = 0
    response = webapp.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )

    return response

@webapp.route('/invalidateKey',methods=['POST'])
def invalidateKey():
    global num_request
    global num_access
    global num_miss
    global num_item
    global current_size

    key = request.form.get('key')
    num_request += 1
    num_access += 1
    if key in memcache:
        value = memcache[key]
        current_size -= sys.getsizeof(value)
        memcache.pop(key)
        num_item -= 1
        response = webapp.response_class(
            response=json.dumps("OK"),
            status=200,
            mimetype='application/json'
        )
    else:
        num_miss += 1
        response = webapp.response_class(
            response=json.dumps("Unknown key"),
            status=400,
            mimetype='application/json'
        )

    return response

@webapp.route('/refreshConfiguration',methods=['POST'])
def refreshConfiguration():
    global policy
    global capacity

    obj = webapp.db_session.query(models.MemcacheConfig).first()
    policy = obj.replacement_policy
    capacity = obj.capacity_in_mb

    response = webapp.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )

    return response


# functions to debug
@webapp.route('/listall',methods=['POST'])
def listall():
    contents = []
    for key in memcache.keys():
        contents.append([key, base64.b64encode(memcache[key]).decode('utf-8')])
        # filee = json.dumps(memcache[key].decode("utf-8"))
    return render_template("image.html", memcache_contents = contents)

@webapp.route('/size',methods=['POST'])
def size():
    response = webapp.response_class(
        response=json.dumps(current_size),
        status=200,
        mimetype='application/json'
    )

    return response

@webapp.route('/stats',methods=['POST'])
def stats():
    msg = ''
    msg += "Capacity: " + str(capacity) + " MB" + ".    "
    msg += "current_size: " + str(current_size) + " bytes"+ ".  "
    msg += "policy: " + policy + ".     "
    msg += "num_item: " + str(num_item) + ".    "
    msg += "num_request: " + str(num_request) + ".      "
    msg += "num_miss: " + str(num_miss) + ".    "
    msg += "num_access: " + str(num_access) + ".    "
    
    response = webapp.response_class(
        response=json.dumps(msg),
        status=200,
        mimetype='application/json'
    )

    return response