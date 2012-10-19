pgbackup is a simple backup manager for postgresql that allows easy uploading to [Amazon web services S3](http://aws.amazon.com/s3/).  

# Step by step

**1. clone this repo:**  
```$ cd ~```  
```$ git clone git://github.com/lucasdavila/pgbackup.git```  
```$ cd pgbackup```  
  
  
**2. Install pip and requiriments:**  
```$ sudo apt-get install python-dev build-essential python-pip```  
```$ sudo sudo pip install --upgrade pip```  
```$ sudo pip install -r requiriments.txt```  
  
  
**3. create your schedules in _/schedules/your_schedule_file_name_:**
<pre>command /usr/bin/pg_dump --host localhost --port 5432 --username "postgres" --format custom --blobs --verbose
--file "%(file)s" data-base-name

# the options below also can be passed via command line when the script backup.py is called (see step 5).

storage_path /home/lucasdavila/pg_backups

aws_s3_credential aws_s3_credential
aws_s3_bucket_name your-bucket-name
aws_s3_storage_key your/remote/path/to/upload</pre>


**4. define your aws credentials in _/schedules/aws_s3_credential_:**
<pre>aws_s3_access_key your-access-key
aws_s3_secret_key your-secret-key</pre>

Remember: Your keys are private, don't add these files into your version control system.


**5. add tasks to crontab, eg:**  
```$ crontab -e```

every sunday at 2:50 AM the remain backups in server will be destroyed  
```50 2 * * 0 rm -r /home/lucasdavila/pg_backups/*.backup```

every day at 2:00 AM the backup will be performed  
```0 2 * * * python /home/lucasdavila/projects/python/pgbackup/backup.py postgresql your_schedule_file_name your_other_schedule```

additionally you can send options in command line with this syntax -Ooption_name=option_value, eg: -Oaws_s3_bucket_name=bucket_name

yep :) now your backup service is working,  you can also perform the backup manually running in terminal:  
 ```$ python /path/to/pgbackup/pg_backup.py my_schedule_name my_other_schedule```
