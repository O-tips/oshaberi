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

def download_file(object_name, file_name=None):
    try:
        client.download_file(bucket_name, object_name, file_name or object_name)
        print(f"Downloaded {object_name} from {bucket_name} to {file_name or object_name}")
    except NoCredentialsError:
        print("Credentials not available.")

# ダウンロード例
download_file("test/remote_file.txt", "local_file.txt")
