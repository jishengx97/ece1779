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

def is_float(element):
    try:
        float(element)
        return True
    except ValueError:
        return False

@webapp.route('/auto_config',methods=['GET'])
def auto_config():
    print(config_mode)
    print(instance_pool)
    return render_template("pages/auto_config/auto_config.html", title = 'Auto Config Cache Pool', 
                            current_size = current_pool_size[0], error_msg = None,
                            max_mr_th = '80', min_mr_th='20', expand_ratio='2', shrink_ratio='0.5')


@webapp.route('/auto_config',methods=['POST'])
def auto_config_post():
    error_msg = ''

    max_mr_input = request.form.get("max_missrate_th")
    min_mr_input = request.form.get("min_missrate_th")
    expand_ratio_input = request.form.get("expand_ratio")
    shrink_ratio_input = request.form.get("shrink_ratio")

    if is_float(max_mr_input) == False or is_float(min_mr_input) == False or is_float(expand_ratio_input) == False or is_float(shrink_ratio_input) == False:
        error_msg = "Please type in a valid float for all parameters!"
        return render_template("pages/auto_config/auto_config.html", title = 'Auto Config Cache Pool', 
                            current_size = current_pool_size[0], error_msg = error_msg,
                            max_mr_th = max_mr_input, min_mr_th=min_mr_input, 
                            expand_ratio=expand_ratio_input, shrink_ratio=shrink_ratio_input)
    
    max_mr_input = float(max_mr_input)
    min_mr_input = float(min_mr_input)
    expand_ratio_input = float(expand_ratio_input)
    shrink_ratio_input = float(shrink_ratio_input)

    if max_mr_input < 0 or max_mr_input >100:
        error_msg = "Max miss rate threshold should be between 0 and 100."
        return render_template("pages/auto_config/auto_config.html", title = 'Auto Config Cache Pool', 
                            current_size = current_pool_size[0], error_msg = error_msg,
                            max_mr_th = max_mr_input, min_mr_th=min_mr_input, 
                            expand_ratio=expand_ratio_input, shrink_ratio=shrink_ratio_input)

    if min_mr_input < 0 or min_mr_input >100:
        error_msg = "Min miss rate threshold should be between 0 and 100."
        return render_template("pages/auto_config/auto_config.html", title = 'Auto Config Cache Pool', 
                            current_size = current_pool_size[0], error_msg = error_msg,
                            max_mr_th = max_mr_input, min_mr_th=min_mr_input, 
                            expand_ratio=expand_ratio_input, shrink_ratio=shrink_ratio_input)
    
    if expand_ratio_input < 1:
        error_msg = "Expand ratio should not be less than 1."
        return render_template("pages/auto_config/auto_config.html", title = 'Auto Config Cache Pool', 
                            current_size = current_pool_size[0], error_msg = error_msg,
                            max_mr_th = max_mr_input, min_mr_th=min_mr_input, 
                            expand_ratio=expand_ratio_input, shrink_ratio=shrink_ratio_input)

    if shrink_ratio_input < 0 or shrink_ratio_input > 1:
        error_msg = "Shrink ratio should be between 0 and 1."
        return render_template("pages/auto_config/auto_config.html", title = 'Auto Config Cache Pool', 
                            current_size = current_pool_size[0], error_msg = error_msg,
                            max_mr_th = max_mr_input, min_mr_th=min_mr_input, 
                            expand_ratio=expand_ratio_input, shrink_ratio=shrink_ratio_input)

    config_mode['mode'] = 'Automatic'
    local_session = webapp.db_session()
    result_count = local_session.query(models.MemcachePoolResizeConfig).count()
    if(result_count == 0):
        new_entry = models.MemcachePoolResizeConfig(
            resize_mode = 'Automatic',
            max_missrate_threshold = max_mr_input,
            min_missrate_threshold = min_mr_input,
            expand_ratio = expand_ratio_input,
            shrink_ratio = shrink_ratio_input,
        )
        local_session.add(new_entry)
        local_session.commit()
    elif(result_count > 1):
        assert False, "the MemcachePoolResizeConfig table should have only one entry!"
    else:
        result = local_session.query(models.MemcachePoolResizeConfig).first()
        result.resize_mode = 'Automatic',
        result.max_missrate_threshold = max_mr_input,
        result.min_missrate_threshold = min_mr_input,
        result.expand_ratio = expand_ratio_input,
        result.shrink_ratio = shrink_ratio_input,
        local_session.commit()

    return render_template("pages/auto_config/auto_config.html", title = 'Auto Config Cache Pool', 
                            current_size = current_pool_size[0], error_msg = 'Successfully switched to automatic mode.',
                            max_mr_th = max_mr_input, min_mr_th=min_mr_input, 
                            expand_ratio=expand_ratio_input, shrink_ratio=shrink_ratio_input)
    

@webapp.route('/auto_config/expand',methods=['POST'])
def auto_config_expand():
    
    expand_ratio = float(request.form.get("ratio"))
#     expand_ratio = 2.0
    print("We have "+str(current_pool_size[0])+" instances currently.")
    pool_size_after_expand = current_pool_size[0] * expand_ratio
    pool_size_after_expand = int(round(pool_size_after_expand))
    if pool_size_after_expand > 8:
        pool_size_after_expand = 8
    instance_to_launch = int(pool_size_after_expand - current_pool_size[0])
    print('need to launch',instance_to_launch)
    
    if instance_to_launch == 0:
        response = webapp.response_class(
                    response=json.dumps('OK'),
                    status=200,
                    mimetype='application/json'
                )
        return response

    client = boto3.client('ec2',
        aws_access_key_id=config('AWSAccessKeyId'), 
        aws_secret_access_key=config('AWSSecretKey'))
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
        MaxCount=instance_to_launch,
        MinCount=1,
        Monitoring={
            'Enabled': False
        },
        SecurityGroupIds=[
            config('SECURITY_GROUP'),
        ]
    )
    
    print(instance_pool)
    new_instance = []
    for instance in response['Instances']:
        new_instance.append(instance['InstanceId'])
        instance_pool.append({'InstanceId' : instance['InstanceId']})


    print("Launched instance num:",len(new_instance))
    print(instance_pool)
    current_pool_size[0] = current_pool_size[0] + len(new_instance)
    print("after expand, current_pool_size", current_pool_size[0])


    # p = Process(target=subprocess_manager, args= (new_instance, ))
    # p.start()

    proc = []

    for instance in new_instance:
        p = Process(target=check_launch_ready, args= (instance, ))
        print('started checking for'+ instance)
        p.start()
        proc.append(p)
    for p in proc:
        p.join()
    print("***all instance setup finish, ready to notify frontend.")

    ip_list = []
    client = boto3.client('ec2',
        aws_access_key_id=config('AWSAccessKeyId'), 
        aws_secret_access_key=config('AWSSecretKey'))
    for instance in new_instance:
        response = client.describe_instances(
            InstanceIds=[
                instance,
            ]
        )
        ip_list.append(response['Reservations'][0]['Instances'][0]['PublicIpAddress'])
    ######## notify frontend this new instance ########
    r = requests.post("http://" + frontend_info['IP'] + ":5000/memcaches/launched", data={'list_string':json.dumps(ip_list ) })
    if r.status_code == 200:
        print('Successfully notify frontend '+frontend_info['IP']+' IP address of memcache ')
        print(new_instance)
        print(ip_list)
    else:
        print('Error: Fail to send memcache ip to frontend.')

    response = webapp.response_class(
                response=json.dumps('OK'),
                status=200,
                mimetype='application/json'
            )
    return response
    

def subprocess_manager(instance_list):

    proc = []

    for instance in instance_list:
        p = Process(target=check_launch_ready, args= (instance, ))
        print('started checking for'+ instance)
        p.start()
        proc.append(p)
    

    for p in proc:
        p.join()
    print("***all instance setup finish, ready to notify frontend.")

    ip_list = []
    client = boto3.client('ec2',
        aws_access_key_id=config('AWSAccessKeyId'), 
        aws_secret_access_key=config('AWSSecretKey'))
    for instance in instance_list:
        response = client.describe_instances(
            InstanceIds=[
                instance,
            ]
        )
        ip_list.append(response['Reservations'][0]['Instances'][0]['PublicIpAddress'])
    ######## notify frontend this new instance ########
    r = requests.post("http://" + frontend_info['IP'] + ":5000/memcaches/launched", data={'list_string':json.dumps(ip_list ) })
    if r.status_code == 200:
        print('Successfully notify frontend '+frontend_info['IP']+' IP address of memcache ')
        print(instance_list)
        print(ip_list)
    else:
        print('Error: Fail to send memcache ip to frontend.')
    
    ###################################################



def check_launch_ready(instance_id):
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


@webapp.route('/auto_config/shrink',methods=['POST'])
def auto_config_shrink():
    global instance_pool
    client = boto3.client('ec2',
        aws_access_key_id=config('AWSAccessKeyId'), 
        aws_secret_access_key=config('AWSSecretKey'))
    ## check all memcache are ready, if not, do not expand or shrink pool
    all_ready = False
    while all_ready == False:
        all_ready = True
        for instance in reversed(instance_pool):
            response = client.describe_instances(
                InstanceIds=[
                    instance['InstanceId'],
                ]
            )
            if response['Reservations'][0]['Instances'][0]['State']['Name'] != 'running':
                print( "Memcache of "+instance['InstanceId']+" is still initializing. Please expand or shrink until initializing complete.")
                all_ready = False
                break
                # response = webapp.response_class(
                #         response=json.dumps('OK'),
                #         status=200,
                #         mimetype='application/json'
                #     )
                # return response

            cache_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
            print('cache IP is '+cache_ip)
            
            try:
                r = requests.post("http://" + cache_ip + ":5000/is_running")
            except:
                print( "Memcache of "+instance['InstanceId']+" is still initializing. Please expand or shrink until initializing complete.")
                all_ready = False
                break
                # response = webapp.response_class(
                #         response=json.dumps('OK'),
                #         status=200,
                #         mimetype='application/json'
                #     )
                # return response
            if r.status_code == 200:
                print("Memcache of "+instance['InstanceId']+" is running.")
            else:
                print( "Memcache of "+instance['InstanceId']+" is still initializing. Please expand or shrink until initializing complete.")
                all_ready = False
                break
                # response = webapp.response_class(
                #         response=json.dumps('OK'),
                #         status=200,
                #         mimetype='application/json'
                #     )
                # return response
        time.sleep(5)

    ################################
    shrink_ratio = float(request.form.get("ratio"))
#     shrink_ratio = 0.5
    print("We have "+str(current_pool_size[0])+" instances currently.")
    pool_size_after_shrink = current_pool_size[0] * shrink_ratio

    pool_size_after_shrink = int(round(pool_size_after_shrink))
    if pool_size_after_shrink < 1:
        pool_size_after_shrink = 1
    instance_to_terminate = int(current_pool_size[0] - pool_size_after_shrink )
    print('need to terminate',instance_to_terminate)

    if instance_to_terminate == 0:
        response = webapp.response_class(
                    response=json.dumps('OK'),
                    status=200,
                    mimetype='application/json'
                )
        return response
    current_pool_size[0] = current_pool_size[0] - instance_to_terminate
    i = instance_to_terminate
    terminate_id = []
    while i > 0:
        terminate_id.append(instance_pool[-1]['InstanceId']) 
        instance_pool.pop()
        i = i -1
    # terminate_id = instance_pool[-instance_to_terminate:]
    # instance_pool = instance_pool[0:-instance_to_terminate]


    r = requests.post("http://" + frontend_info['IP'] + ":5000/memcaches/terminated", data={'terminate_num':json.dumps( instance_to_terminate ) })
    if r.status_code == 200:
        client = boto3.client('ec2',
            aws_access_key_id=config('AWSAccessKeyId'), 
            aws_secret_access_key=config('AWSSecretKey'))
        for id in terminate_id:
            response = client.terminate_instances(
                InstanceIds=[
                    id,
                ]
            )
            print("terminated instance "+id)
        
    else:
        print('Error: frontend disagrees to termiate instance.')
    

    response = webapp.response_class(
                response=json.dumps('OK'),
                status=200,
                mimetype='application/json'
            )
    return response



    
