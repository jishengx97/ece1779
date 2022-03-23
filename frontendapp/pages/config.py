from flask import render_template, url_for, request
from frontendapp import webapp
current_size = 0
max_mr_th = 0
min_mr_th = 0
expand_ratio = 0
shrink_ratio = 0
list_title = "AUTO CONFIG"

@webapp.route('/config',methods=['GET'])
def config_form():
    global list_title
    global current_size
    global max_mr_th
    global min_mr_th
    global expand_ratio
    global shrink_ratio
    error_msg = None
    if list_title=="AUTO CONFIG":
        list_title = "MANUAL CONFIG"
        return render_template("pages/config/config.html", title = list_title, error_msg = None,
                current_size = current_size,max_mr_th = max_mr_th,min_mr_th = min_mr_th,
                expand_ratio = expand_ratio,shrink_ratio = shrink_ratio)
               
    list_title = "AUTO CONFIG"
    return render_template("pages/config/config.html", title = list_title, error_msg = None,
                current_size = current_size,max_mr_th = max_mr_th,min_mr_th = min_mr_th,
                expand_ratio = expand_ratio,shrink_ratio = shrink_ratio)

@webapp.route('/config',methods=['POST'])
def config_post():
    global list_title
    global current_size
    global max_mr_th
    global min_mr_th
    global expand_ratio
    global shrink_ratio
    error_msg = None
    if list_title=="AUTO CONFIG":
        print("do sth relate to the max_mr_th, min_mr_th, expand_ratio, shrink_ratio")
        return render_template("pages/config/config.html", title = list_title, error_msg = None,
                current_size = current_size,max_mr_th = max_mr_th,min_mr_th = min_mr_th,
                expand_ratio = expand_ratio,shrink_ratio = shrink_ratio)

    print("do sth relate to expand and shrink")
    return render_template("pages/config/config.html", title = list_title, error_msg = None,
                current_size = current_size,max_mr_th = max_mr_th,min_mr_th = min_mr_th,
                expand_ratio = expand_ratio,shrink_ratio = shrink_ratio)            

