import boto3
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def download_and_delete_s3_bucket(bucket_name, local_dir):
    # Create an S3 session
    s3 = boto3.resource('s3')
    
    # Access the bucket
    bucket = s3.Bucket(bucket_name)
    
    # Ensure the local directory exists
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    # Iterate over all objects in the bucket
    for obj in bucket.objects.all():
        # Full path to save the file
        local_file_path = os.path.join(local_dir, obj.key)
        
        # Create directories if they don't exist
        if not os.path.exists(os.path.dirname(local_file_path)):
            os.makedirs(os.path.dirname(local_file_path))
        
        # Download the file
        bucket.download_file(obj.key, local_file_path)
        print(f"Downloaded {obj.key} to {local_file_path}")
        
        # Delete the file from S3
        obj.delete()
        print(f"Deleted {obj.key} from S3 bucket")

if __name__ == "__main__":
    # Replace with your S3 bucket name and the directory where you want to save the files
    bucket_name = os.getenv('S3_BUCKET')
    local_dir = os.getenv('LOCAL_DIR')
    
    download_and_delete_s3_bucket(bucket_name, local_dir)
