import os
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readwrite']

def authenticate_google_photos():
    """Authenticate the user and create a service for Google Photos API."""
    flow = InstalledAppFlow.from_client_secrets_file(
        os.getenv('GOOGLE_PHOTOS_CREDENTIALS'), SCOPES)
    
    creds = flow.run_local_server(port=0, prompt='select_account')
    service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)
    return service

def download_and_delete_photos(local_dir):
    """Download and delete all media from Google Photos."""
    service = authenticate_google_photos()
    
    # Create the local directory if it does not exist
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    # Get all media items from Google Photos
    media_items = []
    next_page_token = None
    while True:
        results = service.mediaItems().list(pageSize=100, pageToken=next_page_token).execute()
        media_items.extend(results.get('mediaItems', []))
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break

    # Download and delete each media item
    for item in media_items:
        media_url = item['baseUrl'] + '=d'  # Add '=d' to download the media in original quality
        media_id = item['id']
        file_name = item['filename']

        # Download the file
        response = requests.get(media_url)
        local_file_path = os.path.join(local_dir, file_name)

        with open(local_file_path, 'wb') as f:
            f.write(response.content)
            print(f"Downloaded {file_name} to {local_file_path}")

        # Delete the media item from Google Photos
        service.mediaItems().delete(mediaItemId=media_id).execute()
        print(f"Deleted {file_name} from Google Photos")

if __name__ == "__main__":
    local_dir = os.getenv('GOOGLE_LOCAL_DIR')
    download_and_delete_photos(local_dir)
