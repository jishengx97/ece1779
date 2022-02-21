from flask import render_template, url_for, request
from frontendapp import webapp
from flask import json
def is_float(element):
    try:
        float(element)
        return True
    except ValueError:
        return False


@webapp.route('/config',methods=['GET'])
def config_form():
    return render_template("pages/config/config_form.html", title = "CONFIG", error_msg = None)

@webapp.route('/config',methods=['POST'])
def config_save():
    error_msg = None

    capacity_input = request.form.get("capacity_input")

    if is_float(capacity_input) == False:
        error_msg = "Please type in a valid float"
        return render_template("pages/config/config_form.html", title = "CONFIG", error_msg = error_msg)

    capacity_input = float(capacity_input)

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

    return render_template("pages/config/config_form.html", title = "CONFIG", error_msg = error_msg)