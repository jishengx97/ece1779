#!/bin/bash
# This is the bash script to automatically pull new updates,
# enter python virtual environment and run the webapps. 

# Before handing in the project remember to create a copy
# of this script in the home directory because this is checked
# in to the repository.

# Uncomment this line when copied to the home directory
cd ~/ece1779/

# Default to not pulling from git because it's getting annoying :)
if [ "$1" = "pull_latest" ]; then
    echo "> Pulling newest updates from repository"
    git checkout -f
    git pull
fi

# Properly kill gunicorn processes that are still running
kill -9 `ps aux | grep gunicorn | grep run_frontendapp | awk '{print $2}'`
kill -9 `ps aux | grep gunicorn | grep run_memcacheapp | awk '{print $2}'`

echo "> Starting virtual environment and installing new packages"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# # It is important to launch memcache app first because it is setting up the database
echo "> Starting the memcache app on port 5001"
gunicorn --bind 0.0.0.0:5001 --timeout 0 --workers=1 --threads=2 --capture-output --log-level debug run_memcacheapp:webapp &> memcacheapp_log.txt &

# Wait a bit to allow setup to properly finish
sleep 2

echo "> Starting the frontend app on port 5000"
gunicorn --bind 0.0.0.0:5000 --timeout 0 --workers=1 --threads=2 --capture-output --log-level debug run_frontendapp:webapp &> frontendapp_log.txt &

# Wait a bit to allow setup to properly finish
sleep 2

# echo "> Starting the managercache app on port 5000"
# gunicorn --bind 0.0.0.0:5000 --timeout 0 --workers=1 --threads=2 --capture-output --log-level debug run_managerapp:webapp &> managerapp_log.txt &

# # Wait a bit to allow setup to properly finish
# sleep 2
