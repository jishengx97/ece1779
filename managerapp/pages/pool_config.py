from managerapp import webapp, current_pool_size,instance_pool,frontend_info,config_mode
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

list_title = "MANUAL CONFIG"

@webapp.route('/pool_config',methods=['GET'])
def pool_config_form():
    global list_title
    error_msg = None
    print(instance_pool)
    print(config_mode)
    if config_mode['mode'] == 'Automatic':
        list_title = "AUTO CONFIG"
    else:
        list_title = "MANUAL CONFIG"
  
    
    if list_title=="AUTO CONFIG":
        local_session = webapp.db_session()
        result = local_session.query(models.MemcachePoolResizeConfig).first()

        return render_template("pages/pool_config/pool_config.html", title = list_title, error_msg = None,
                current_size = current_pool_size[0],max_mr_th = result.max_missrate_threshold,min_mr_th = result.min_missrate_threshold,
                expand_ratio = result.expand_ratio,shrink_ratio = result.shrink_ratio)
               
    
    return render_template("pages/pool_config/pool_config.html", title = list_title, error_msg = None,
                current_size = current_pool_size[0],max_mr_th = 80,min_mr_th = 20,
                expand_ratio = 2.0,shrink_ratio =  0.5)

@webapp.route('/pool_config',methods=['POST'])
def pool_config_post():
    global list_title
    if request.form['action'] == 'SWITCH TO MANUAL CONFIG':
        list_title = "MANUAL CONFIG"
        return render_template("pages/pool_config/pool_config.html", title = list_title, error_msg = None,
                current_size = current_pool_size[0],max_mr_th = 80,min_mr_th = 20,
                expand_ratio = 2.0,shrink_ratio = 0.5) 

    elif request.form['action'] == 'SWITCH TO AUTO CONFIG':
        list_title = "AUTO CONFIG"
        local_session = webapp.db_session()
        result = local_session.query(models.MemcachePoolResizeConfig).first()

        return render_template("pages/pool_config/pool_config.html", title = list_title, error_msg = None,
                current_size = current_pool_size[0],max_mr_th = result.max_missrate_threshold,min_mr_th = result.min_missrate_threshold,
                expand_ratio = result.expand_ratio,shrink_ratio = result.shrink_ratio)
        

    elif request.form['action'] == 'expand':
        r = requests.post("http://127.0.0.1:5000/manual_config", data={'action':'expand'})
        print(r.content)
        return render_template("pages/pool_config/pool_config.html", title = list_title, error_msg = (r.content.decode('UTF-8')),
                current_size = current_pool_size[0],max_mr_th = 80,min_mr_th = 20,
                expand_ratio = 2.0,shrink_ratio =  0.5)

        
    elif request.form['action'] == 'shrink':
        r = requests.post("http://127.0.0.1:5000/manual_config", data={'action':'shrink'})
        print(r.content)
        return render_template("pages/pool_config/pool_config.html", title = list_title, error_msg = (r.content.decode('UTF-8')),
                current_size = current_pool_size[0],max_mr_th = 80,min_mr_th = 20,
                expand_ratio = 2.0,shrink_ratio =  0.5)
    elif request.form['action'] == 'submit':
        r = requests.post("http://127.0.0.1:5000/auto_config", data={'max_missrate_th':request.form.get("max_missrate_th"),
                                                                    'min_missrate_th':request.form.get("min_missrate_th"),
                                                                    'expand_ratio':request.form.get("expand_ratio"),
                                                                    'shrink_ratio':request.form.get("shrink_ratio") })

        return render_template("pages/pool_config/pool_config.html", title = list_title, error_msg = r.content.decode('UTF-8'),
                current_size = current_pool_size[0],max_mr_th = request.form.get("max_missrate_th"),min_mr_th = request.form.get("min_missrate_th"),
                expand_ratio = request.form.get("expand_ratio"),shrink_ratio =  request.form.get("shrink_ratio"))
    else:
        print("not ok")