# app.py

from flask import Flask, render_template, request, redirect, url_for, flash
import boto3
from config import Config
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Initialize the S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
    region_name=Config.S3_REGION
)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'files' not in request.files:
            flash('No files part')
            return redirect(request.url)
        
        files = request.files.getlist('files')

        if len(files) == 0 or files[0].filename == '':
            flash('No selected files')
            return redirect(request.url)

        for file in files:
            if file:
                file_name = file.filename
                s3_client.upload_fileobj(file, Config.S3_BUCKET, file_name)
                flash(f'{file_name} successfully uploaded to S3')

        return redirect(url_for('index'))

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
