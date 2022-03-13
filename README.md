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

To setup S3 bucket:
1. Search S3 on AWS console, choose Scalable Storage in the Cloud
2. Click orange button "create bucket".
3. Enter the bucket name. Note, this name must be unique for all buckets in the region(us-east-1).
4. Select region to "US East (N.Virginia) us-east-1"
5. Other default option for other settings.

To setup AWS RDS:
1. Search rds and choose "Managed Relational Database Service"
2. Click the orange button "create database"
3. Choose "mysql" as engine, and version 8.0.27
4. Templates, choose "Free tier"
5. In settings, enter databse name (ece1779project), enter username(root), enter password.
6. In connectivity, VPC: Select Default VPC. set "public access" to Yes. VPC Security Group(s): select "default"
7. Use "password authentication"
8. Click "create database"
9. Open the database just created, in "Connectivity & security" section, under "Endpoint & port", you can find the endpoint of your database. 
10. In the "security group rules", click the security group with "inbound" type
11. Click inbound rules, and click edit inbound rules
12. Add rules to allow all the inbound traffic. Type "All traffic", source to "Anywhere IPv6" and "Anywhere IPv4", save rules
13. Use the following command in local machine to test whether you can connect to the database
```mysql -h {endpoint address} -P 3306 -u root -p```
14. Modify the database url in common/database.py 
```DATABASE_URL = "mysql+pymysql://{user_name}:{password}@{endpoint}:3306/{database_name}"```
