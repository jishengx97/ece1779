from flask import render_template, url_for, request
from frontendapp import webapp
from flask import json


@webapp.route('/api/upload',methods=['GET'])
def upload_form():
    return render_template("api/upload/upload_form.html",title = "UPLOAD")