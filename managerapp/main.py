
from flask import render_template, url_for, request
from managerapp import webapp,instance_pool,current_pool_size,frontend_info,memcache_info
from flask import json
import boto3   
import time
import paramiko
import requests
from multiprocessing.dummy import Process

@webapp.route('/',methods=['GET'], strict_slashes=False)
def main():

    return render_template("main.html",title = "Welcome to cache manager")


@webapp.before_first_request
def before_first_request_func():
    print('before_first_request function running')

@webapp.after_request
def disable_cache(response):
    response.cache_control.max_age = 0
    response.cache_control.public = True
    return response


