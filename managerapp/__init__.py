from flask import Flask, _app_ctx_stack
from sqlalchemy.orm import scoped_session
# from common import database
from decouple import config
import multiprocessing
from decouple import config
import boto3
# manager = multiprocessing.Manager()
# instance_pool = manager.list()
instance_pool = []
webapp = Flask(__name__)
webapp.url_map.strict_slashes = False
current_pool_size = [1]
frontend_info = {}
memcache_info = {}

frontend_info['InstanceId'] = config('FRONTEND_ID')
memcache_info['InstanceId'] = config('MEMCACHE_ID')

client = boto3.client('ec2', region_name='us-east-1')
response = client.describe_instances(
    InstanceIds=[
        frontend_info['InstanceId'],
        memcache_info['InstanceId'],
    ]
)
frontend_info['DNS'] = response['Reservations'][0]['Instances'][0]['PublicDnsName']
memcache_info['DNS'] = response['Reservations'][1]['Instances'][0]['PublicDnsName']

frontend_info['IP'] = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
memcache_info['IP'] = response['Reservations'][1]['Instances'][0]['PublicIpAddress']
instance_pool.append({'InstanceId':config('MEMCACHE_ID')})
from managerapp import main
from managerapp.pages import pool_stats, manual_config


