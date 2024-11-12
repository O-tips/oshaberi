import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError

# .envファイルの読み込み
load_dotenv()

# 環境変数の取得
endpoint_url = os.getenv("ENDPOINT_URL")
access_key = os.getenv("ACCESS_KEY")
secret_key = os.getenv("SECRET_KEY")
bucket_name = os.getenv("BUCKET_NAME")

# クライアント設定
session = boto3.session.Session()
client = session.client('s3',
                        region_name='nyc3',
                        endpoint_url=endpoint_url,
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key)

# アップロード関数の例
def upload_file(file_name, object_name=None):
    try:
        client.upload_file(file_name, bucket_name, object_name or file_name)
        print(f"Uploaded {file_name} to {bucket_name}/{object_name or file_name}")
    except NoCredentialsError:
        print("Credentials not available.")

# アップロード例
upload_file("assets/local_file.txt", "test/remote_file.txt")
