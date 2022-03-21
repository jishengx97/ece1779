from managerapp import webapp, current_pool_size,instance_pool,frontend_info,config_mode
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
import paramiko
from common import models

@webapp.route('/manual_config',methods=['GET'])
def manual_config():
    print(instance_pool)
    print(config_mode)
    # global current_pool_size
    return render_template("pages/manual_config/manual_config.html", title = 'Manually Config Cache Pool', current_size = current_pool_size[0], error_msg = None)


@webapp.route('/manual_config',methods=['POST'])
def manual_config_post():
    # global current_pool_size
    client = boto3.client('ec2',
        aws_access_key_id=config('AWSAccessKeyId'), 
        aws_secret_access_key=config('AWSSecretKey'))
    error_msg = ''
    ## check all memcache are ready, if not, do not expand or shrink pool
    for instance in reversed(instance_pool):
        response = client.describe_instances(
            InstanceIds=[
                instance['InstanceId'],
            ]
        )
        if response['Reservations'][0]['Instances'][0]['State']['Name'] != 'running':
            error_msg = "Memcache of "+instance['InstanceId']+" is still initializing. Please expand or shrink until initializing complete."
            print( "Memcache of "+instance['InstanceId']+" is still initializing. Please expand or shrink until initializing complete.")
            return render_template("pages/manual_config/manual_config.html", title = 'Manually Config Cache Pool', current_size = current_pool_size[0], error_msg = error_msg)


        cache_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
        print('cache IP is '+cache_ip)
        
        try:
            r = requests.post("http://" + cache_ip + ":5000/is_running")
        except:
            error_msg = "Memcache of "+instance['InstanceId']+" is still initializing. Please expand or shrink until initializing complete."
            print( "Memcache of "+instance['InstanceId']+" is still initializing. Please expand or shrink until initializing complete.")
            return render_template("pages/manual_config/manual_config.html", title = 'Manually Config Cache Pool', current_size = current_pool_size[0], error_msg = error_msg)

        if r.status_code == 200:
            print("Memcache of "+instance['InstanceId']+" is running.")
        else:
            error_msg = "Memcache of "+instance['InstanceId']+" is still initializing. Please expand or shrink until initializing complete."
            print( "Memcache of "+instance['InstanceId']+" is still initializing. Please expand or shrink until initializing complete.")
            return render_template("pages/manual_config/manual_config.html", title = 'Manually Config Cache Pool', current_size = current_pool_size[0], error_msg = error_msg)


    ################################
    
    config_mode['mode'] = 'Manual'

    local_session = webapp.db_session()
    result_count = local_session.query(models.MemcachePoolResizeConfig).count()
    if(result_count == 0):
        new_entry = models.MemcachePoolResizeConfig(
            resize_mode = 'Manual',
            max_missrate_threshold = 80,
            min_missrate_threshold = 20,
            expand_ratio = 2,
            shrink_ratio = 0.5,
        )
        local_session.add(new_entry)
        local_session.commit()
    elif(result_count > 1):
        assert False, "the MemcachePoolResizeConfig table should have only one entry!"
    else:
        result = local_session.query(models.MemcachePoolResizeConfig).first()
        result.resize_mode = 'Manual'
        local_session.commit()

    action = request.form['action']
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
            KeyName=config('KEY_NAME'),
            MaxCount=1,
            MinCount=1,
            Monitoring={
                'Enabled': False
            },
            SecurityGroupIds=[
                config('SECURITY_GROUP'),
            ]
        )
        
        print(response['Instances'][0]['InstanceId'])
        print(response['Instances'][0]['State']['Name'])
        
        new_instance ={}
        new_instance['InstanceId'] = response['Instances'][0]['InstanceId']
        instance_pool.append(new_instance)

        error_msg = 'Launching new memcache instance.'
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
    # global pending_instance
    time.sleep(3) ### call describe_instances() right after run_instances() will get error, so we need to sleep a while, so AWS can initilize the new instance 
    client = boto3.client('ec2',
        aws_access_key_id=config('AWSAccessKeyId'), 
        aws_secret_access_key=config('AWSSecretKey'))
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

    new_cache_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connected = False
    while connected == False:
        try:
            # connect
            client.connect(new_cache_ip, username='ubuntu', key_filename=config('PEM_PATH'))
            connected = True
        except:
            print("connection fails. Sleeping")
            time.sleep(2)
    
    
    stdin, stdout, stderr = client.exec_command('git clone https://github.com/jishengx97/ece1779.git')
    print(stdout.readlines())
    print(stderr.readlines())

    ftp = client.open_sftp()
    ftp.put('/home/ubuntu/ece1779/.env', '/home/ubuntu/ece1779/.env')

    stdin, stdout, stderr = client.exec_command('cd ece1779; chmod 700 start_memcache.sh; ./start_memcache.sh')
    print(stderr.readlines())
    print(stdout.readlines())

    client.close()



    ######## notify frontend this new instance ########
    r = requests.post("http://" + frontend_info['IP'] + ":5000/memcaches/launched", data={'list_string':json.dumps([ new_cache_ip ] ) })
    if r.status_code == 200:
        print('Successfully notify frontend '+frontend_info['IP']+' IP address of memcache '+ new_cache_ip)
    else:
        print('Error: Fail to send memcache ip to frontend.')
    
    ###################################################

def notify_and_terminate(instance_id):
   
    ## notify frontend  ##########

    r = requests.post("http://" + frontend_info['IP'] + ":5000/memcaches/terminated", data={'terminate_num':json.dumps( instance_id ) })
    if r.status_code == 200:
        print('Successfully notify frontend '+frontend_info['IP']+' to terminate the last '+ str(instance_id)+' instance.')
    else:
        print('Error: Fail to send terminate request to frontend.')

    #########################################
        
    client = boto3.client('ec2',
        aws_access_key_id=config('AWSAccessKeyId'), 
        aws_secret_access_key=config('AWSSecretKey'))
    response = client.terminate_instances(
        InstanceIds=[
            instance_id,
        ]
    )
    print("terminated instance "+instance_id)


    

