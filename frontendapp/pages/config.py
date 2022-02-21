from flask import render_template, url_for, request
from frontendapp import webapp
from flask import json
from common import models
def is_float(element):
    try:
        float(element)
        return True
    except ValueError:
        return False


@webapp.route('/config',methods=['GET'])
def config_form():
    obj = webapp.db_session.query(models.MemcacheConfig).first()
    init_policy = obj.replacement_policy
    init_capacity = obj.capacity_in_mb
    return render_template("pages/config/config_form.html", title = "CONFIG", policys = ["LRU", "RANDOM"], init_capacity = init_capacity, init_policy = init_policy, error_msg = None)

@webapp.route('/config',methods=['POST'])
def config_save():
    error_msg = None

    obj = webapp.db_session.query(models.MemcacheConfig).first()
    init_policy = obj.replacement_policy
    init_capacity = obj.capacity_in_mb

    capacity_input = request.form.get("capacity_input")
    policy_input = request.form.get('policy_input')

    if is_float(capacity_input) == False:
        error_msg = "Please type in a valid float"
        return render_template("pages/config/config_form.html", title = "CONFIG", policys = ["LRU", "RANDOM"], init_capacity = init_capacity, init_policy = init_policy, error_msg = error_msg)

    capacity_input = float(capacity_input)
    
    if capacity_input == init_capacity and policy_input == init_capacity:
        error_msg = "Error nothing changed"
        return render_template("pages/config/config_form.html", title = "CONFIG", policys = ["LRU", "RANDOM"], init_capacity = init_capacity, init_policy = init_policy, error_msg = error_msg)
    # if capacity_input == "":
    #     error_msg = "Missing key"
    #     return render_template("pages/key/key_form.html",title = "KEY",error_msg = error_msg, img = None)

    # r = requests.post("http://127.0.0.1:5001/get", data={'key':key_input})

    # if r.status_code == 200:
    #     error_msg = "KEY SUCCESS"
    #     img = r.json()
    # else:
    #     error_msg = r.json()
    #     img = None

    return render_template("pages/config/config_form.html", title = "CONFIG", policys = ["LRU", "RANDOM"], init_capacity = init_capacity, init_policy = init_policy, error_msg = error_msg)