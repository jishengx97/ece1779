from flask import render_template, url_for, request
from frontendapp import webapp
from flask import json
from common import models

@webapp.route('/list_keys',methods=['GET'])
def list_keys_form():
    local_session = webapp.db_session()
    result = local_session.query(models.KeyAndFileLocation)
    return render_template("pages/list_keys/list_keys_form.html", title = "LIST_KEYS", lists = result, error_msg = None)