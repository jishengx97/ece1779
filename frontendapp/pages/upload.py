from flask import render_template, url_for, request
from frontendapp import webapp
from flask import json


@webapp.route('/upload',methods=['GET'])
def upload_form():
    return render_template("pages/upload/upload_form.html",title = "UPLOAD")

@webapp.route('/upload',methods=['POST'])
def upload_save():
    error_msg = None
    key_input = request.form.get("key_input")
    if key_input == "":
        error_msg = "Missing key"
        return render_template("pages/upload/upload_form.html",title = "UPLOAD",error_msg = error_msg)
    
    if 'uploadedfile' not in request.files:
        error_msg = "Missing uploaded file"
        return render_template("pages/upload/upload_form.html",title = "UPLOAD",error_msg = error_msg)
    
    new_file = request.files['uploadedfile']

    if new_file.filename == '':
        error_msg = "Missing file name"
        return render_template("pages/upload/upload_form.html",title = "UPLOAD",error_msg = error_msg)
    
    # tempdir = tempfile.gettempdir()
    # new_file.save(os.path.join(tempdir,new_file.filename))

    error_msg = "UPLOAD SUCCESS"
    return render_template("pages/upload/upload_form.html",title = "UPLOAD",error_msg = error_msg)