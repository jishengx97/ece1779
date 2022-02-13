from flask import render_template, url_for, request
from frontendapp import webapp
from flask import json


@webapp.route('/get',methods=['GET'])
def get_form():
    return render_template("get/get_form.html",title = "Get")