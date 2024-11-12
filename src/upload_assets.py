import boto3
from botocore.exceptions import NoCredentialsError

# DigitalOcean Spacesの情報
endpoint_url = "https://custom-ar-assets.nyc3.digitaloceanspaces.com"
access_key = "YOUR_ACCESS_KEY"
secret_key = "YOUR_SECRET_KEY"
bucket_name = "YOUR_BUCKET_NAME"

# クライアント設定
session = boto3.session.Session()
client = session.client('s3',
                        region_name='nyc3',
                        endpoint_url=endpoint_url,
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key)

def upload_file(file_name, object_name=None):
    try:
        client.upload_file(file_name, bucket_name, object_name or file_name)
        print(f"Uploaded {file_name} to {bucket_name}/{object_name or file_name}")
    except NoCredentialsError:
        print("Credentials not available.")

# アップロード例
upload_file("local_file.txt", "remote_file.txt")
