#!/bin/bash
# This is the bash script to automatically pull new updates,
# enter python virtual environment and run the webapps. 

# Before handing in the project remember to create a copy
# of this script in the home directory because this is checked
# in to the repository.

# Uncomment this line when copied to the home directory
# cd ~/ece1779/

echo "> Pulling newest updates from repository"
git checkout -f
git pull

echo "> Starting virtual environment and installing new packages"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Kill any process that's sitting on the ports now
sudo kill -9 `sudo lsof -t -i:5000`
sudo kill -9 `sudo lsof -t -i:5001`

echo "> Starting the memcache app on port 5001"
gunicorn --bind 0.0.0.0:5001 --workers=1 run_memcacheapp:webapp &> memcacheapp_log.txt &

echo "> Starting the frontend app on port 5000"
gunicorn --bind 0.0.0.0:5000 --workers=1 run_frontendapp:webapp &> frontendapp_log.txt &