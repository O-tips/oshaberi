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

def download_file(object_name, file_name=None):
    try:
        client.download_file(bucket_name, object_name, file_name or object_name)
        print(f"Downloaded {object_name} from {bucket_name} to {file_name or object_name}")
    except NoCredentialsError:
        print("Credentials not available.")

# ダウンロード例
download_file("remote_file.txt", "local_file.txt")
