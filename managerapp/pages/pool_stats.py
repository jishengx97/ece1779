from managerapp import webapp, current_pool_size,instance_pool

import requests
from flask import render_template, url_for, request
from flask import json
import os
# from common import models
import re
import boto3
from decouple import config


@webapp.route('/pool_stats',methods=['GET'])
def pool_stats  ():
    print(instance_pool)
    # global current_pool_size
    # current_pool_size = current_pool_size + 1
    return render_template("pages/pool_stats/pool_stats.html", title = 'Diplay Current Pool Stats',  current_size = current_pool_size[0], error_msg = None)

