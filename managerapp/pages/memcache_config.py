from flask import render_template, url_for, request
from managerapp import webapp, current_pool_size,instance_pool
from flask import json
from common import models
import requests
import boto3    
from decouple import config
config_title = "Change Memcache Configurations"
choice1 = "Least Recently Used"
choice2 = "Random"

def is_float(element):
    try:
        float(element)
        return True
    except ValueError:
        return False


@webapp.route('/memcache_config',methods=['GET'])
def memcache_config():
    local_session = webapp.db_session()
    obj = local_session.query(models.MemcacheConfig).first()
    init_policy = obj.replacement_policy
    init_capacity = obj.capacity_in_mb
    return render_template("pages/memcache_config/memcache_config.html", title = config_title, policys = [choice1, choice2], init_capacity = init_capacity, init_policy = init_policy, error_msg = None)

@webapp.route('/memcache_config',methods=['POST'])
def memcache_config_save():
    error_msg = None

    local_session = webapp.db_session()
    obj = local_session.query(models.MemcacheConfig).first()
    init_policy = obj.replacement_policy
    init_capacity = obj.capacity_in_mb

    if (request.form['action'] == 'clear all memcache'):
        # send clear to all memcache in the pool
        client = boto3.client('ec2',
            aws_access_key_id=config('AWSAccessKeyId'), 
            aws_secret_access_key=config('AWSSecretKey'))
        error_msg = ''
        for instance in instance_pool:
            response = client.describe_instances(
                InstanceIds=[
                    instance['InstanceId'],
                ]
            )

            cache_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
            print('cache IP is '+cache_ip)

            r = requests.post("http://" + cache_ip + ":5000/clear")
            if r.status_code == 200:
                error_msg += 'CLEAR  CACHE FOR INSTANCE ' + instance['InstanceId']
            else:
                error_msg += r.json()
        return render_template("pages/memcache_config/memcache_config.html", title = config_title, policys = [choice1, choice2], init_capacity = init_capacity, init_policy = init_policy, error_msg = error_msg)
    
    if (request.form['action'] == 'clear S3 and RDS storage'):
        error_msg = 'Clear S3 and RDS storage.'
        ###############################
        #send request to frontend to clear
        ###############################
        return render_template("pages/memcache_config/memcache_config.html", title = config_title, policys = [choice1, choice2], init_capacity = init_capacity, init_policy = init_policy, error_msg = error_msg)
    
    
    capacity_input = request.form.get("capacity_input")
    policy_input = request.form.get('policy_input')
    if(policy_input == choice1):
        policy_input = "LRU"
    else:
        policy_input = "Random"

    if is_float(capacity_input) == False:
        error_msg = "Please type in a valid float for capacity!"
        return render_template("pages/memcache_config/memcache_config.html", title = config_title, policys = [choice1, choice2], init_capacity = init_capacity, init_policy = init_policy, error_msg = error_msg)

    capacity_input = float(capacity_input)
    
    if capacity_input == init_capacity and policy_input == init_policy:
        error_msg = "Nothing changed for configuration!"
        return render_template("pages/memcache_config/memcache_config.html", title = config_title, policys = [choice1, choice2], init_capacity = init_capacity, init_policy = init_policy, error_msg = error_msg)
    
    obj.capacity_in_mb = capacity_input
    obj.replacement_policy = policy_input
    local_session.commit()

    # send refreshConfiguration to all memcache in the pool
    client = boto3.client('ec2',
        aws_access_key_id=config('AWSAccessKeyId'), 
        aws_secret_access_key=config('AWSSecretKey'))
    error_msg = ''
    for instance in instance_pool:
        response = client.describe_instances(
            InstanceIds=[
                instance['InstanceId'],
            ]
        )

        cache_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
        print('cache IP is '+cache_ip)

        r = requests.post("http://" + cache_ip + ":5000/refreshConfiguration")
        if r.status_code == 200:
            error_msg += 'CONFIG SUCCESS FOR INSTANCE ' + instance['InstanceId']
        else:
            error_msg += r.json()


    return render_template("pages/memcache_config/memcache_config.html", title = config_title, policys = [choice1, choice2], init_capacity = capacity_input, init_policy = policy_input, error_msg = error_msg)


