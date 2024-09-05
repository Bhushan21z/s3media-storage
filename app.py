import os
import boto3
import google.auth
from flask import Flask, render_template, request, flash, redirect, url_for, session
from config import Config
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import requests

app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# OAuth Scopes for Google Photos API
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly', 
          'https://www.googleapis.com/auth/photoslibrary.appendonly']

# Allow insecure transport for local development (disable in production)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def get_google_photos_service():
    if 'credentials' not in session:
        return None

    creds = Credentials(
        token=session['credentials']['token'],
        refresh_token=session['credentials'].get('refresh_token'),
        token_uri=session['credentials']['token_uri'],
        client_id=session['credentials']['client_id'],
        client_secret=session['credentials']['client_secret'],
        scopes=session['credentials']['scopes']
    )

    return build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

def upload_to_google_photos(files):
    service = get_google_photos_service()

    if not service:
        flash("You need to login to Google Photos first!")
        return redirect(url_for('login'))

    for file in files:
        file_name = file.filename
        # Upload media to Google Photos
        upload_token = upload_media_to_google_photos(service, file, file_name)
        if upload_token:
            create_media_item(service, upload_token, file_name)
            flash(f'Successfully uploaded {file_name} to Google Photos!')

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
        flash(f"Failed to upload {file_name} to Google Photos")
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

def upload_to_s3(files):
    s3 = boto3.client(
        's3',
        aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=app.config['S3_REGION']
    )
    for file in files:
        file_name = file.filename
        s3.upload_fileobj(file, app.config['S3_BUCKET'], file_name)
        flash(f'Successfully uploaded {file_name} to S3!')

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
        upload_to_google_photos(files)

    return render_template('google_upload.html', google_signed_in=google_signed_in)

@app.route('/s3_upload', methods=['GET', 'POST'])
def s3_upload():
    if request.method == 'POST':
        storage_service = request.form.get('storage-service')

        if storage_service == 's3':
            files = request.files.getlist('file')
            upload_to_s3(files)
        elif storage_service == 'gphotos':
            return redirect(url_for('login'))
        else:
            flash('Invalid storage service selected!')

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
    app.run(port=5000, debug=True)
