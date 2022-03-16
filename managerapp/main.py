
from flask import render_template, url_for, request
from managerapp import webapp,instance_pool,current_pool_size
from flask import json
import boto3   
import time

@webapp.route('/',methods=['GET'], strict_slashes=False)
def main():
    print(instance_pool)
    return render_template("main.html",title = "Welcome to cache manager")


@webapp.before_first_request
def before_first_request_func():
    print('before_first_request function running')
    #launch the first memcache instance
    # client = boto3.client('ec2', region_name='us-east-1')
    # response = client.run_instances(
    #     BlockDeviceMappings=[
    #         {
    #             'DeviceName': '/dev/sda1',
    #             'Ebs': {

    #                 'DeleteOnTermination': True,
    #                 'VolumeSize': 8,
    #                 'VolumeType': 'gp2',
    #                 'Encrypted': False
    #             },
    #         },
    #     ],
    #     ImageId='ami-080ff70d8f5b80ba5',
    #     InstanceType='t2.micro',
    #     KeyName='samuel_ece1779',
    #     MaxCount=1,
    #     MinCount=1,
    #     Monitoring={
    #         'Enabled': False
    #     },
    #     SecurityGroupIds=[
    #         'sg-0e1432edaa6860df2',
    #     ],
    #     SubnetId='subnet-07a75a35b48bd500c',
    # )

    # print('Launched first memcache instance')
    # print(response['Instances'][0])
    # print(response['Instances'][0]['InstanceId'])
    # print(response['Instances'][0]['State']['Name'])

    # new_instance ={}
    # new_instance['InstanceId'] = response['Instances'][0]['InstanceId']
    
    # time.sleep(2)
    # response = client.describe_instances(
    #     InstanceIds=[
    #         new_instance['InstanceId'],
    #     ]
    # )

    # print(response['Reservations'][0]['Instances'][0]['InstanceId'])

    # print(response['Reservations'][0]['Instances'][0]['PublicDnsName'])
    # print(response['Reservations'][0]['Instances'][0]['PublicIpAddress'])

    # new_instance['State'] = response['Reservations'][0]['Instances'][0]['State']['Name']
    # new_instance['DNS'] = response['Reservations'][0]['Instances'][0]['PublicDnsName']
    # new_instance['IP'] = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
    # instance_pool.append(new_instance)

    ##### nofity the frontend this new instance ######

    ##################################################



@webapp.after_request
def disable_cache(response):
    response.cache_control.max_age = 0
    response.cache_control.public = True
    return response

#@webapp.teardown_appcontext
#def teardown_db(exception=None):
#    webapp.db_session.remove()

