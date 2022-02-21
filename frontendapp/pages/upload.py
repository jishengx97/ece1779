import requests
from flask import render_template, url_for, request
from frontendapp import webapp
from flask import json


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
    
    if 'uploadedfile' not in request.files:
        error_msg = "Missing uploaded file"
        return render_template("pages/upload/upload_form.html", title = "UPLOAD", error_msg = error_msg)
    
    new_file = request.files['uploadedfile']

    if new_file.filename == '':
        error_msg = "Missing file name"
        return render_template("pages/upload/upload_form.html", title = "UPLOAD", error_msg = error_msg)

    local_session = webapp.db_session()
    result = local_session.query(models.KeyAndFileLocation).filter(models.KeyAndFileLocation.key == key_input)
    if(result.count() == 1):
        # key exists, update file, send invalidate request
        r = requests.post("http://127.0.0.1:5001/invalidateKey", data={'key':key_input,})
    else:
        # key doesn't exist, create new entry
        new_entry = models.KeyAndFileLocation(
            key = key_input,
            file_location = "file_location"
        )
        local_session.add(new_entry)
        local_session.commit()
        # must refresh before accessing
        local_session.refresh(new_entry)
        print(new_entry.id)
        # use new_entry.id here

    if r.status_code == 200:
        error_msg = "UPLOAD SUCCESS"
    else:
        error_msg = r.json()  
    return render_template("pages/upload/upload_form.html", title = "UPLOAD", error_msg = error_msg)