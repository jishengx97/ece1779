
from flask import render_template, url_for, request
from frontendapp import webapp
from flask import json


@webapp.route('/',methods=['GET'])
def main():
    return render_template("main.html",title = "Main")