from flask import render_template, url_for, request
from frontendapp import webapp
from flask import json


@webapp.route('/upload',methods=['GET'])
def upload_form():
    return render_template("upload/upload_form.html",title = "Upload")