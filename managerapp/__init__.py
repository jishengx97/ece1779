from flask import Flask, _app_ctx_stack
from sqlalchemy.orm import scoped_session
from common import database
from decouple import config
import multiprocessing
from decouple import config
import boto3
import requests
from flask import json
import sys
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

client = boto3.client('ec2',
        aws_access_key_id=config('AWSAccessKeyId'), 
        aws_secret_access_key=config('AWSSecretKey'))
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

######notify frontend the first memcache
r = requests.post("http://" + frontend_info['IP'] + ":5000/memcaches/launched", data={'list_string':json.dumps([ memcache_info['IP'] ] ) })
if r.status_code == 200:
    print('Successfully notify frontend '+frontend_info['IP']+' IP address of memcache '+memcache_info['IP'])
else:
    print('Fail to send memcache ip to frontend. Exit.')
    sys.exit(0)
##########################################
database.init_db()
webapp.db_session = scoped_session(database.SessionLocal, scopefunc=_app_ctx_stack.__ident_func__)

from managerapp import initialize_db
initialize_db.set_db_default_values()
from managerapp import main
from managerapp.pages import pool_stats, manual_config, memcache_config


