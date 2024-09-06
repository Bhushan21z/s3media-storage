# config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    STORAGE_SERVICE = os.getenv('STORAGE_SERVICE', 's3')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    S3_BUCKET = os.getenv('S3_BUCKET')
    S3_REGION = os.getenv('S3_REGION')
    GOOGLE_PHOTOS_CREDENTIALS_FILE = '/tmp/google_photos_credentials.json'
