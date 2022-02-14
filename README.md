# ece1779 Course Project
A1: web development

To run on EC2:

        # To run without pulling the latest changes
        ./start.sh
        # To pull the latest changes from the repository, and then run
        ./start.sh pull_latest
        
This bash script will launch two gunicorn instances, for the frontend app to run on port 5000 and the memcache app to run on port 5001.
