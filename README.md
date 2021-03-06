dbbackup is a simple backup manager for postgresql that allows easy upload to [Amazon web services S3](http://aws.amazon.com/s3/).  

# Step by step

**1. clone this repo:**  
```$ cd ~```  
```$ git clone git://github.com/lucasdavila/dbbackup.git```  
```$ cd dbbackup```  
  
  
**2. Install pip and requirements:**  
```$ sudo apt-get install python-dev build-essential python-pip```  
```$ sudo sudo pip install --upgrade pip```  
```$ sudo pip install -r requirements.txt```  
  
  
**3. create your schedules in _/schedules/your_schedule_file_name_:**
<pre>command /usr/bin/pg_dump --no-password --host localhost --port 5432 --username "postgres" --format custom --blobs --verbose
--file "%(file)s" data-base-name

# the options below also can be passed via command line when the script backup.py is called (see step 5).  

storage_path /home/lucasdavila/backups/database/%(year)s/%(month)s

aws_s3_credential aws_s3_credential
aws_s3_bucket_name your-bucket-name
aws_s3_storage_key your/remote/path/to/upload/%(year)s/%(month)s</pre>


**4. define your aws credentials in _/schedules/aws_s3_credential_:**
<pre>aws_s3_access_key your-access-key
aws_s3_secret_key your-secret-key</pre>

Remember: Your keys are private, don't add these files into your version control system.
  
  
**5. add tasks to crontab, eg:**  
```$ crontab -e```  

if your server require a password, you can define the postgres user password  
```PGPASSWORD=123```  

every day call logrotate to rotates dbbackup logs  
```45 2 * * * cd /home/lucasdavila/projects/python/dbbackup; logrotate -s logs/logrotate_state logs/logrotate_config;```  

every sunday at 2:50 AM the remain backups in server will be destroyed  
```50 2 * * 0 rm -r /home/lucasdavila/backups/database/*.backup```

every day at 2:00 AM the backup will be performed  
```0 2 * * * python /home/lucasdavila/projects/python/dbbackup/backup.py postgresql your_schedule_file_name your_other_schedule```

additionally you can send options in command line with this syntax -Ooption_name=option_value, eg: -Oaws_s3_bucket_name=bucket_name

yep :) now your backup service is working,  you can also perform the backup manually running in terminal:  
 ```$ python /path/to/dbbackup/backup.py my_schedule_name my_other_schedule```
