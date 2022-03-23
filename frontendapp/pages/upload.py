import requests
from flask import render_template, url_for, request
from frontendapp import webapp, s3_bucket_name, lock_S3, lock_RDS
from flask import json
import os
from common import models
import re
import boto3
from decouple import config
upload_title = "Upload Key and Image Pair"

@webapp.route('/upload',methods=['GET'])
def upload_form():
    return render_template("pages/upload/upload_form.html", title = upload_title, error_msg = None)

@webapp.route('/upload',methods=['POST'])
def upload_save():
    error_msg = None
    key_input = request.form.get("key_input")
    if key_input == "":
        error_msg = "Please specify a key!"
        return render_template("pages/upload/upload_form.html", title = upload_title, error_msg = error_msg)
    if len(key_input) > 120:
        error_msg = "Key should be less than 120 characters long!"
        return render_template("pages/upload/upload_form.html", title = upload_title, error_msg = error_msg)
    if  re.match("^[A-Za-z0-9_-]*$", key_input) == None:
        error_msg = "Please only use upper and lower-case letters, numbers, dashes and underscores in key!"
        return render_template("pages/upload/upload_form.html", title = upload_title, error_msg = error_msg)
    if 'uploadedfile' not in request.files:
        error_msg = "Please upload an image file!"
        return render_template("pages/upload/upload_form.html", title = upload_title, error_msg = error_msg)

    new_file = request.files['uploadedfile']

    if new_file.filename == '':
        error_msg = "Please specify a file with a filename!"
        return render_template("pages/upload/upload_form.html", title = upload_title, error_msg = error_msg)
    ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif'}
    file_filename, file_extension = os.path.splitext(new_file.filename)
    if (file_extension.lower() in ALLOWED_EXTENSIONS) == False:
        error_msg = "Only .jpg, .jpeg, .png and .gif formats are allowed!"
        return render_template("pages/upload/upload_form.html", title = upload_title, error_msg = error_msg)
    lock_RDS.acquire()
    lock_S3.acquire()
    local_session = webapp.db_session()
    client = boto3.client('s3',aws_access_key_id=config('AWSAccessKeyId'), aws_secret_access_key=config('AWSSecretKey'))
    result = local_session.query(models.KeyAndFileLocation).filter(models.KeyAndFileLocation.key == key_input)
    if(result.count() == 1):
        # key exists, update file, send invalidate request
        client.delete_object(Bucket=s3_bucket_name, Key=result.first().file_location)
        # os.remove(result.first().file_location)
        new_file.filename = str(result.first().id)+file_extension 
        client.put_object(Body=new_file, Bucket=s3_bucket_name, Key='test/'+new_file.filename)
        # new_file.save(os.path.join("/home/ubuntu/ece1779/images", new_file.filename))
        result.first().file_location = "test/"+new_file.filename
        r = requests.post("http://127.0.0.1:5000/memcaches/invalidateKey", data={'key':key_input,})
        if r.status_code == 200:
            error_msg = "Key already exists, updated image."
        else:
            error_msg = r.json()   
    else:
        # key doesn't exist, create new entry

        new_entry = models.KeyAndFileLocation(
            key = key_input,
            file_location = "wangha78"
        )
        local_session.add(new_entry)
        local_session.commit()
        # must refresh before accessing
        local_session.refresh(new_entry)
        # if not os.path.exists("/home/ubuntu/ece1779/images"):
        #     os.makedirs("/home/ubuntu/ece1779/images")
        new_file.filename = str(new_entry.id)+file_extension    
        client.put_object(Body=new_file, Bucket=s3_bucket_name, Key='test/'+new_file.filename)
        # new_file.save(os.path.join("/home/ubuntu/ece1779/images", new_file.filename))
        new_entry.file_location = "test/"+new_file.filename
        local_session.commit()
        r = requests.post("http://127.0.0.1:5000/memcaches/invalidateKey", data={'key':key_input,})
        if r.status_code == 200:
            error_msg = "Successfully uploaded the key and image pair!"
        else:
            error_msg = r.json()
    lock_RDS.release()
    lock_S3.release()       
    return render_template("pages/upload/upload_form.html", title = upload_title, error_msg = error_msg)




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
    ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif'}
    file_filename, file_extension = os.path.splitext(new_file.filename)
    if (file_extension.lower() in ALLOWED_EXTENSIONS) == False:
        data = {"success": "false","error": {"code" : "400", "message":"Only .jpg, .jpeg, .png and .gif formats are allowed!"}}
        response = webapp.response_class(
                response=json.dumps(data),
                status=400,
                mimetype='application/json'
            )
        return response

    lock_RDS.acquire()
    lock_S3.acquire()
    local_session = webapp.db_session()
    client = boto3.client('s3',aws_access_key_id=config('AWSAccessKeyId'), aws_secret_access_key=config('AWSSecretKey'))
    result = local_session.query(models.KeyAndFileLocation).filter(models.KeyAndFileLocation.key == key_input)
    if(result.count() == 1):
        # key exists, update file, send invalidate request
        client.delete_object(Bucket=s3_bucket_name, Key=result.first().file_location)
        new_file.filename = str(result.first().id)+file_extension 
        client.put_object(Body=new_file, Bucket=s3_bucket_name, Key='test/'+new_file.filename)
        result.first().file_location = "test/"+new_file.filename
        r = requests.post("http://127.0.0.1:5000/memcaches/invalidateKey", data={'key':key_input,})
        
    else:
        # key doesn't exist, create new entry
        new_entry = models.KeyAndFileLocation(
            key = key_input,
            file_location = "wangha78"
        )
        local_session.add(new_entry)
        local_session.commit()
        # must refresh before accessing
        local_session.refresh(new_entry)
        new_file.filename = str(new_entry.id)+file_extension    
        client.put_object(Body=new_file, Bucket=s3_bucket_name, Key='test/'+new_file.filename)
        new_entry.file_location = "test/"+new_file.filename
        local_session.commit()
        r = requests.post("http://127.0.0.1:5000/memcaches/invalidateKey", data={'key':key_input,})
    lock_RDS.release()
    lock_S3.release()
    data = {"success": "true"}
    response = webapp.response_class(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )
    return response
