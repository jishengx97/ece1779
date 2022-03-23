
from flask import render_template, url_for, request
from memcacheapp import webapp, memcache,capacity,policy,current_size,num_item,num_request,num_miss,num_access,lock
from flask import json
from common import models
import random
import base64
import sys
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from pytz import timezone
import boto3
from botocore.exceptions import ClientError
from decouple import config
from ec2_metadata import ec2_metadata

def print_cache_stats():
    global num_request
    global num_access
    global num_miss
    # msg = ''
    # msg += "Capacity: " + str(capacity) + " MB" + ".    "
    # msg += "current_size: " + str(current_size) + " bytes"+ ".  "
    # msg += "policy: " + policy + ".     "
    # msg += "num_item: " + str(num_item) + ".    "
    # msg += "num_request: " + str(num_request) + ".      "
    # msg += "num_miss: " + str(num_miss) + ".    "
    # msg += "num_access: " + str(num_access) + ".    "

    # Miss rate and hit rate in percentage
    if num_access > 0:
        miss_rate = num_miss / num_access * 100
        hit_rate = (num_request - num_miss) / num_access * 100
    else:
        miss_rate = 0.0
        hit_rate = 0.0
    # msg += "miss rate: " + str(miss_rate) + "%.    "
    # msg += "hit rate: " + str(hit_rate) + "%.    "

    eastern = timezone('US/Eastern')
    current_time = datetime.now(eastern)
    # msg += "curent time: " + current_time.strftime("%X") + ".    "
    # print(msg)

    # print("Writing to CloudWatch Custom Metrics")
    cw_client = boto3.client('cloudwatch', 
        aws_access_key_id=config('AWSAccessKeyId'), 
        aws_secret_access_key=config('AWSSecretKey')
    )
    metric_namespace = 'ece1779-a2-memcache-stats'
    dimentions = [
        {
            'Name': 'InstanceID',
            'Value': ec2_metadata.instance_id
        },
    ]

    # publish the actual datapoint
    metric_data = []
    metric_name = 'num_miss'
    metric_data.append(
        {
            'MetricName': metric_name,
            'Value': num_miss,
            'Timestamp': current_time,
            'Dimensions': dimentions,
            'StorageResolution': 1,
        })

    metric_name = 'num_access'
    metric_data.append(
        {
            'MetricName': metric_name,
            'Value': num_access,
            'Timestamp': current_time,
            'Dimensions': dimentions,
            'StorageResolution': 1,
        })


    metric_name = 'num_request'
    metric_data.append(
        {
            'MetricName': metric_name,
            'Value': num_request,
            'Timestamp': current_time,
            'Dimensions': dimentions,
            'StorageResolution': 1,
        })

    metric_name = 'num_item'
    metric_data.append(
        {
            'MetricName': metric_name,
            'Value': num_item,
            'Timestamp': current_time,
            'Dimensions': dimentions,
            'StorageResolution': 1,
        })

    metric_name = 'current_size'
    metric_data.append(
        {
            'MetricName': metric_name,
            'Value': current_size,
            'Timestamp': current_time,
            'Dimensions': dimentions,
            'StorageResolution': 1,
        })

    metric_name = 'num_workers'
    metric_data.append(
        {
            'MetricName': metric_name,
            'Value': 1,
            'Timestamp': current_time,
            'Dimensions': dimentions,
            'StorageResolution': 1,
        })

    response = cw_client.put_metric_data(
        Namespace=metric_namespace,
        MetricData=metric_data,
    )

    lock.acquire()
    try:
        num_miss = 0
        num_access = 0
        num_request = 0
    finally:
        lock.release()


@webapp.route('/')
def main():

    return render_template("main.html")

@webapp.route('/get',methods=['POST'])
def get():
    global num_request
    global num_access
    global num_miss

    key = request.form.get('key')

    lock.acquire()
    try:
        num_request += 1
        num_access += 1
    finally:
        lock.release()
    
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
        lock.acquire()
        try:
            num_miss += 1
        finally:
            lock.release()
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
    value = request.files['image'].read()
    new_size = sys.getsizeof(value)
    
    lock.acquire()
    try:
        num_request += 1
    finally:
        lock.release()
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
    lock.acquire()
    try:
        num_request += 1
        current_size = 0   
        num_item = 0
    finally:
        lock.release()
    memcache.clear()     
    response = webapp.response_class(
        response=json.dumps("OK"),
        status=200, 
        mimetype='application/json'
    )

    return response

@webapp.route('/invalidateKey',methods=['POST'])
def invalidateKey():
    global num_request
    # global num_access
    # global num_miss
    global num_item
    global current_size

    key = request.form.get('key')
    lock.acquire()
    try:
        num_request += 1
    finally:
        lock.release()
    # num_access += 1
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
        # num_miss += 1
        response = webapp.response_class(
            response=json.dumps("OK"),
            status=200,
            mimetype='application/json'
        )

    return response

@webapp.route('/refreshConfiguration',methods=['POST'])
def refreshConfiguration():
    global policy
    global capacity
    global num_request
    global current_size
    global num_item
    lock.acquire()
    try:
        num_request += 1
    finally:
        lock.release()
    local_session = webapp.db_session()
    obj = local_session.query(models.MemcacheConfig).first()
    policy = obj.replacement_policy
    capacity = obj.capacity_in_mb


    while current_size > capacity * 1024 * 1024:
        if policy == 'LRU':
            least_recent_entry = memcache.popitem(last = False) 
            current_size -= sys.getsizeof(least_recent_entry[1])
            num_item -= 1
        else:
            removekey = random.choice(list(memcache.keys()))
            current_size -= sys.getsizeof(memcache[removekey])
            memcache.pop(removekey)
            num_item -= 1


    response = webapp.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )

    return response

@webapp.route('/is_running',methods=['POST'])
def is_running():
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

@webapp.teardown_appcontext
def teardown_db(exception=None):
    webapp.db_session.remove()
