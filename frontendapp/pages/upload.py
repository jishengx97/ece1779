import requests
from flask import render_template, url_for, request
from frontendapp import webapp
from flask import json
import os
from common import models
import re
@webapp.route('/upload',methods=['GET'])
def upload_form():
    return render_template("pages/upload/upload_form.html", title = "UPLOAD", error_msg = None)

@webapp.route('/upload',methods=['POST'])
def upload_save():
    error_msg = None
    key_input = request.form.get("key_input")
    if key_input == "":
        error_msg = "Missing key"
        return render_template("pages/upload/upload_form.html", title = "UPLOAD", error_msg = error_msg)
    if len(key_input) > 120:
        error_msg = "Key size should be less than 120"
        return render_template("pages/upload/upload_form.html", title = "UPLOAD", error_msg = error_msg)
    if  re.match("^[A-Za-z0-9_-]*$", key_input) == None:
        error_msg = "Please do not use special character"
        return render_template("pages/upload/upload_form.html", title = "UPLOAD", error_msg = error_msg)
    if 'uploadedfile' not in request.files:
        error_msg = "Missing uploaded file"
        return render_template("pages/upload/upload_form.html", title = "UPLOAD", error_msg = error_msg)

    new_file = request.files['uploadedfile']

    if new_file.filename == '':
        error_msg = "Missing file name"
        return render_template("pages/upload/upload_form.html", title = "UPLOAD", error_msg = error_msg)
    ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif'}
    file_filename, file_extension = os.path.splitext(new_file.filename)
    if (file_extension.lower() in ALLOWED_EXTENSIONS) == False:
        error_msg = "Only allow jpg jpeg png gif"
        return render_template("pages/upload/upload_form.html", title = "UPLOAD", error_msg = error_msg)
    local_session = webapp.db_session()
    result = local_session.query(models.KeyAndFileLocation).filter(models.KeyAndFileLocation.key == key_input)
    if(result.count() == 1):
        # key exists, update file, send invalidate request
        os.remove(result.first().file_location)
        new_file.filename = str(result.first().id)+file_extension 
        new_file.save(os.path.join("/home/ubuntu/ece1779/images", new_file.filename))
        result.first().file_location = "/home/ubuntu/ece1779/images/"+new_file.filename
        r = requests.post("http://127.0.0.1:5001/invalidateKey", data={'key':key_input,})
        if r.status_code == 200:
            error_msg = "KEY ALREADY EXIST SUCCESS UPDATE THE IMAGE"
        else:
            error_msg = r.json()   
    else:
        # key doesn't exist, create new entry
        new_entry = models.KeyAndFileLocation(
            key = key_input,
            file_location = "/home/ubuntu/ece1779/images"
        )
        local_session.add(new_entry)
        local_session.commit()
        # must refresh before accessing
        local_session.refresh(new_entry)
        if not os.path.exists("/home/ubuntu/ece1779/images"):
            os.makedirs("/home/ubuntu/ece1779/images")
        new_file.filename = str(new_entry.id)+file_extension    
        new_file.save(os.path.join("/home/ubuntu/ece1779/images", new_file.filename))
        new_entry.file_location = "/home/ubuntu/ece1779/images/"+new_file.filename
        local_session.commit()
        r = requests.post("http://127.0.0.1:5001/invalidateKey", data={'key':key_input,})
        if r.status_code == 200:
            error_msg = "SUCCESS UPLOAD THE NEW IMAGE"
        else:
            error_msg = r.json()
    return render_template("pages/upload/upload_form.html", title = "UPLOAD", error_msg = error_msg)




@webapp.route('/api/upload',methods=['POST'])
def test_upload():
    key_input = request.form['key']
    if key_input == "":
        data = {"success": "false", "error": {"code" : "400", "message":"key is missing."}}
        response = webapp.response_class(
                response=json.dumps(data),
                status=400,
                mimetype='application/json'
            )
        return response
    if 'file' not in request.files:
        data = {"success": "false","error": {"code" : "400", "message":"file is missing."}}
        response = webapp.response_class(
                response=json.dumps(data),
                status=400,
                mimetype='application/json'
            )
        return response
    new_file = request.files['file']
    if new_file.filename == '':
        data = {"success": "false","error": {"code" : "400", "message":"file is missing."}}
        response = webapp.response_class(
                response=json.dumps(data),
                status=400,
                mimetype='application/json'
            )
        return response

    local_session = webapp.db_session()
    file_filename, file_extension = os.path.splitext(new_file.filename)
    result = webapp.db_session.query(models.KeyAndFileLocation).filter(models.KeyAndFileLocation.key == key_input)
    if(result.count() == 1):
        # key exists, update file, send invalidate request
        os.remove(result.first().file_location)
        new_file.filename = str(result.first().id)+file_extension 
        new_file.save(os.path.join("/home/ubuntu/ece1779/images", new_file.filename))
        result.first().file_location = "/home/ubuntu/ece1779/images/"+new_file.filename
        r = requests.post("http://127.0.0.1:5001/invalidateKey", data={'key':key_input,})
        
    else:
        # key doesn't exist, create new entry
        new_entry = models.KeyAndFileLocation(
            key = key_input,
            file_location = "/home/ubuntu/ece1779/images"
        )
        local_session.add(new_entry)
        local_session.commit()
        # must refresh before accessing
        local_session.refresh(new_entry)
        if not os.path.exists("/home/ubuntu/ece1779/images"):
            os.makedirs("/home/ubuntu/ece1779/images")
        new_file.filename = str(new_entry.id)+file_extension    
        new_file.save(os.path.join("/home/ubuntu/ece1779/images", new_file.filename))
        new_entry.file_location = "/home/ubuntu/ece1779/images/"+new_file.filename
        local_session.commit()
        r = requests.post("http://127.0.0.1:5001/invalidateKey", data={'key':key_input,})

    data = {"success": "true"}
    response = webapp.response_class(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )
    return response
