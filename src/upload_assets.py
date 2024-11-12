import os
from dotenv import load_dotenv
import aiofiles
import aioboto3
from botocore.exceptions import NoCredentialsError
import asyncio

# .envファイルの読み込み
load_dotenv()

# 環境変数の取得
endpoint_url = os.getenv("ENDPOINT_URL")
access_key = os.getenv("ACCESS_KEY")
secret_key = os.getenv("SECRET_KEY")
bucket_name = os.getenv("BUCKET_NAME")

# アップロード関数
async def upload_fileobj(file_obj, object_name=None):
    try:
        # aioboto3セッションの開始
        async with aioboto3.session.Session().client('s3',
                                                   region_name='nyc3',
                                                   endpoint_url=endpoint_url,
                                                   aws_access_key_id=access_key,
                                                   aws_secret_access_key=secret_key) as client:
            # ファイルオブジェクトを直接渡してアップロード
            await client.upload_fileobj(file_obj, bucket_name, object_name)
            print(f"Uploaded {object_name} to bucket {bucket_name}")
    except NoCredentialsError:
        print("Credentials not available.")
    except Exception as e:
        print(f"Error occurred: {e}")
