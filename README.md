pgbackup is a simple backup manager for postgresql that allows easy uploading to [Amazon web services S3](http://aws.amazon.com/s3/).

# Step by step

**1. clone this repo:**  
```$ cd ~  
$ git clone git://github.com/lucasdavila/pgbackup.git  
$ cd pgbackup```


**2. Install pip and requiriments:**  
```$ sudo apt-get install python-dev build-essential python-pip```    
```$ sudo sudo pip install --upgrade pip```    
```$ sudo pip install -r requiriments.txt```    
    
  
**3. create your schedules in _/schedules/your_schedule_file_name_:**  
```command /usr/bin/pg_dump --host localhost --port 5432 --username "postgres" --format custom --blobs --verbose --file "%(file)s" data-base-name```    
```manager my_super_manager_name```  
```storage_path /home/lucasdavila/pg_backups```  
```aws_s3_credential aws_s3_credential```  
```aws_s3_bucket_name your-bucket-name```  
```aws_s3_storage_key your/remote/path/to/upload```  
  
  
**4. define your aws credentials in _/schedules/aws_s3_credential_:**  
```aws_s3_access_key your-access-key```  
```aws_s3_secret_key your-secret-key```  
Remember: Your keys are private. DON'T add this into your version control system.
  
  
**5. add a crontab:**  
```$ crontab -e```  
```15 13 * * * python /home/lucasdavila/projects/python/pgbackup/backup.py postgresql your_schedule_file_name your_other_schedule```  

yep :) now your backup service is working.

### todo
- replace manager by email options in schedule files.  

Note: to test the backup manually just run this command ```$ python /path/to/pgbackup/pg_backup.py my_schedule_name my_other_schedule```
