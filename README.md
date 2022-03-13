# ece1779 Course Project
A1: web development

To run on EC2:

        # To run without pulling the latest changes
        ./start.sh
        # To pull the latest changes from the repository, and then run
        ./start.sh pull_latest
        
This bash script will launch two gunicorn instances, for the frontend app to run on port 5000 and the memcache app to run on port 5001.

A2: Dynamic Resource Management

To setup cloudwatch:
1. On the AWS management console, search for "AWS Cloud Map" in the search bar on the top left corner
2. Click on "Create namespace"
3. Create a namesapce called "ece1779-a2-memcache-stats", this is the assumed name in the codebase.
