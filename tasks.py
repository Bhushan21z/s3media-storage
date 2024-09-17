import os
import boto3
from celery_worker import celery
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import requests

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

@celery.task
def upload_file_to_google_photos(file_path, file_name, credentials_info):
    # Initialize Google Photos API client with user credentials
    creds = Credentials(
        token=credentials_info['token'],
        refresh_token=credentials_info.get('refresh_token'),
        token_uri=credentials_info['token_uri'],
        client_id=credentials_info['client_id'],
        client_secret=credentials_info['client_secret'],
        scopes=credentials_info['scopes']
    )
    
    service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

    # Read the file to be uploaded
    with open(file_path, 'rb') as file:
        upload_token = upload_media_to_google_photos(service, file, file_name)
        if upload_token:
            create_media_item(service, upload_token, file_name)
    
    # Remove the temporary file after upload
    os.remove(file_path)

def upload_media_to_google_photos(service, file, file_name):
    upload_url = "https://photoslibrary.googleapis.com/v1/uploads"
    headers = {
        "Authorization": f"Bearer {service._http.credentials.token}",
        "Content-Type": "application/octet-stream",
        "X-Goog-Upload-File-Name": file_name,
        "X-Goog-Upload-Protocol": "raw",
    }
    response = requests.post(upload_url, headers=headers, data=file.read())
    if response.status_code == 200:
        return response.text  # Upload token
    else:
        print(f"Failed to upload {file_name} to Google Photos: {response.status_code}")
        return None

def create_media_item(service, upload_token, file_name):
    new_media_item = {
        "newMediaItems": [
            {
                "simpleMediaItem": {
                    "uploadToken": upload_token
                }
            }
        ]
    }
    service.mediaItems().batchCreate(body=new_media_item).execute()
