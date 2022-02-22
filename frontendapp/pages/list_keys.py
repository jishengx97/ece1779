from flask import render_template, url_for, request
from frontendapp import webapp
from flask import json
from common import models
list_title = "List all Known Keys"

@webapp.route('/list_keys',methods=['GET'])
def list_keys_form():
    error_msg = None
    local_session = webapp.db_session()
    result = local_session.query(models.KeyAndFileLocation)
    if(result.count() == 0):
        return render_template("pages/list_keys/list_keys_form.html", title = list_title, lists = result, error_msg = "No keys are known yet!")
    return render_template("pages/list_keys/list_keys_form.html", title = list_title, lists = result, error_msg = None)


@webapp.route('/api/list_keys',methods=['POST'])
def test_list_keys():
    local_session = webapp.db_session()
    result = local_session.query(models.KeyAndFileLocation)
    key_list = []
    for r in result:
        key_list.append(r.key)
    data = {"keys": key_list,
            "success": "true"}
    response = webapp.response_class(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )
    return response
