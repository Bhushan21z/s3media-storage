import os
import boto3
from flask import Flask, render_template, request, flash, redirect, url_for, session
from config import Config
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import requests
import json
from werkzeug.utils import secure_filename
import uuid
from celery_worker import make_celery
from tasks import upload_file_to_s3
from tasks import upload_file_to_google_photos

app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = 'tmp/uploads'

google_credentials = os.getenv('GOOGLE_PHOTOS_CREDENTIALS')
if google_credentials:
    with open('/tmp/google_photos_credentials.json', 'w') as creds_file:
        creds_file.write(google_credentials)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure Celery
app.config['CELERY_BROKER_URL'] = app.config['REDIS_URL']
app.config['CELERY_RESULT_BACKEND'] = app.config['REDIS_URL']
celery = make_celery(app)

# OAuth Scopes for Google Photos API
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly', 
          'https://www.googleapis.com/auth/photoslibrary.appendonly']

# Allow insecure transport for local development (disable in production)
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

@app.route('/login')
def login():
    # Create OAuth flow instance
    flow = Flow.from_client_secrets_file(
        app.config['GOOGLE_PHOTOS_CREDENTIALS_FILE'], 
        scopes=SCOPES,
        redirect_uri=url_for('oauth_callback', _external=True)
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth_callback')
def oauth_callback():
    state = session['state']
    
    flow = Flow.from_client_secrets_file(
        app.config['GOOGLE_PHOTOS_CREDENTIALS_FILE'], 
        scopes=SCOPES, 
        state=state,
        redirect_uri=url_for('oauth_callback', _external=True)
    )

    flow.fetch_token(authorization_response=request.url)
    
    credentials = flow.credentials

    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    session['google_signed_in'] = True
    return redirect(url_for('google_upload'))

@app.route('/google_upload', methods=['GET', 'POST'])
def google_upload():
    if 'credentials' not in session:
        return redirect(url_for('login'))

    google_signed_in = session.get('google_signed_in', False)
    if request.method == 'POST':
        files = request.files.getlist('file')
        credentials = session['credentials']
        for file in files:
            if file:
                file_name = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
                file.save(file_path)
                upload_file_to_google_photos.delay(file_path, file_name, credentials)

        flash('Files are being processed and will be uploaded to Google Photos shortly!')

    return render_template('google_upload.html', google_signed_in=google_signed_in)

@app.route('/s3_upload', methods=['GET', 'POST'])
def s3_upload():
    if request.method == 'POST':
        files = request.files.getlist('file')
        for file in files:
            if file:
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                upload_file_to_s3.delay(
                        file_path, 
                        filename,
                        app.config['AWS_ACCESS_KEY_ID'],
                        app.config['AWS_SECRET_ACCESS_KEY'],
                        app.config['S3_REGION'],
                        app.config['S3_BUCKET']
                    )
        flash('Files are being processed and will be uploaded to S3 shortly!')
    return render_template('s3_upload.html')

@app.route('/ipfs_upload', methods=['GET', 'POST'])
def ipfs_upload():
    return render_template('ipfs_upload.html')

@app.route('/ftp_upload', methods=['GET', 'POST'])
def ftp_upload():
    return render_template('ftp_upload.html')

@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('s3_upload'))

if __name__ == '__main__':
    app.run(port=5000, debug=False)
