import os
import boto3
from celery_worker import celery

@celery.task
def upload_file_to_s3(file_path, file_name, aws_access_key_id, aws_secret_access_key, s3_region, s3_bucket):
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=s3_region
    )
    with open(file_path, 'rb') as file:
        s3.upload_fileobj(file, s3_bucket, file_name)
    os.remove(file_path)  # Remove the temporary file after upload
