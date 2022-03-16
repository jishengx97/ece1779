from managerapp import webapp, current_pool_size,pending_instance,instance_pool
from managerapp.pages import pool_stats
import requests
from flask import render_template, url_for, request
from flask import json
import os
# from common import models
import re
import boto3    
from decouple import config
from multiprocessing.dummy import Process
import time

@webapp.route('/manual_config',methods=['GET'])
def manual_config():
    print(instance_pool)
    # global current_pool_size
    return render_template("pages/manual_config/manual_config.html", title = 'Manually Config Cache Pool', current_size = current_pool_size[0], error_msg = None)


@webapp.route('/manual_config',methods=['POST'])
def manual_config_post():
    global pending_instance
    # global current_pool_size

    error_msg = None
    action = request.form['action']
    client = boto3.client('ec2', region_name='us-east-1')
    if action == 'expand':
        if current_pool_size[0] >= 8:
            error_msg = 'Reach max pool size. Cannot expand more.'
            return render_template("pages/manual_config/manual_config.html", title = 'Manually Config Cache Pool', current_size = current_pool_size[0], error_msg = error_msg)

        # current_pool_size = current_pool_size + 1
        current_pool_size[0] += 1
        response = client.run_instances(
            BlockDeviceMappings=[
                {
                    'DeviceName': '/dev/sda1',
                    'Ebs': {

                        'DeleteOnTermination': True,
                        'VolumeSize': 8,
                        'VolumeType': 'gp2',
                        'Encrypted': False
                    },
                },
            ],
            ImageId='ami-080ff70d8f5b80ba5',
            InstanceType='t2.micro',
            KeyName='samuel_ece1779',
            MaxCount=1,
            MinCount=1,
            Monitoring={
                'Enabled': False
            },
            SecurityGroupIds=[
                'sg-0e1432edaa6860df2',
            ],
            SubnetId='subnet-07a75a35b48bd500c',
        )
        
        print(response['Instances'][0]['InstanceId'])
        print(response['Instances'][0]['State']['Name'])
        
        pending_instance = pending_instance + 1
        new_instance ={}
        new_instance['InstanceId'] = response['Instances'][0]['InstanceId']
        instance_pool.append(new_instance)

        error_msg = 'Launching new memcache instance.'
        # time.sleep(2)
        p = Process(target=check_launch_and_notify, args= (response['Instances'][0]['InstanceId'], ))
        p.start()

    elif action == 'shrink':
        if current_pool_size[0] == 1:
            error_msg = 'Reach min pool size. Cannot shrink more.'
            return render_template("pages/manual_config/manual_config.html", title = 'Manually Config Cache Pool', current_size = current_pool_size[0], error_msg = error_msg)
        
        # current_pool_size = current_pool_size - 1
        current_pool_size[0] -= 1
        terminate_id = instance_pool[-1]['InstanceId']
        instance_pool.pop()
        p = Process(target=notify_and_terminate, args= (terminate_id, ))
        p.start()

        error_msg = 'Terminating cache instance.'
    else:
        error_msg = 'invalid input action'

     
    return render_template("pages/manual_config/manual_config.html", title = 'Manually Config Cache Pool', current_size = current_pool_size[0], error_msg = error_msg)


def check_launch_and_notify(instance_id):
    print("subprocess starts")
    global pending_instance
    time.sleep(3) ### call describe_instances() right after run_instances() will get error, so we need to sleep a while, so AWS can initilize the new instance 
    client = boto3.client('ec2', region_name='us-east-1')
    response = client.describe_instances(
        InstanceIds=[
            instance_id,
        ]
    )
    state = response['Reservations'][0]['Instances'][0]['State']['Name']


    while state != 'running':
        time.sleep(5) 
        response = client.describe_instances(
            InstanceIds=[
                instance_id,
            ]
        )

        state = response['Reservations'][0]['Instances'][0]['State']['Name']
    
    print('Instance is ready, ' + instance_id)
    print(response['Reservations'][0]['Instances'][0]['State']['Name'])
    print(response['Reservations'][0]['Instances'][0]['PublicDnsName'])
    print(response['Reservations'][0]['Instances'][0]['PublicIpAddress'])

    # new_instance ={}
    # new_instance['InstanceId'] = response['Reservations'][0]['Instances'][0]['InstanceId']
    # new_instance['State'] = response['Reservations'][0]['Instances'][0]['State']['Name']
    # new_instance['DNS'] = response['Reservations'][0]['Instances'][0]['PublicDnsName']
    # new_instance['IP'] = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
    # pending_instance  = pending_instance - 1
    # instance_pool.append(new_instance)
    # print(instance_pool)

    ######## notify frontend this new instance ########
    
    ###################################################

def notify_and_terminate(instance_id):
    client = boto3.client('ec2', region_name='us-east-1')
    while(0): ## notify frontend, until ready to terminate
        time.sleep(5)

    response = client.terminate_instances(
        InstanceIds=[
            instance_id,
        ]
    )
    print("terminated instance "+instance_id)


    

