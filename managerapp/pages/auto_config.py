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

    config_mode['mode'] = 'Auto'
    local_session = webapp.db_session()
    result_count = local_session.query(models.MemcachePoolResizeConfig).count()
    if(result_count == 0):
        new_entry = models.MemcachePoolResizeConfig(
            resize_mode = 'Auto',
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
        result.resize_mode = 'Auto',
        result.max_missrate_threshold = max_mr_input,
        result.min_missrate_threshold = min_mr_input,
        result.expand_ratio = expand_ratio_input,
        result.shrink_ratio = shrink_ratio_input,
        local_session.commit()

    return render_template("pages/auto_config/auto_config.html", title = 'Auto Config Cache Pool', 
                            current_size = current_pool_size[0], error_msg = 'Successfully switched to automatic mode.',
                            max_mr_th = max_mr_input, min_mr_th=min_mr_input, 
                            expand_ratio=expand_ratio_input, shrink_ratio=shrink_ratio_input)
    

