import os
from dotenv import load_dotenv
import aioboto3, aiofiles, io
from botocore.exceptions import NoCredentialsError
import asyncio

# .envファイルの読み込み
load_dotenv()

# 環境変数の取得
endpoint_url = os.getenv("ENDPOINT_URL")
access_key = os.getenv("ACCESS_KEY")
secret_key = os.getenv("SECRET_KEY")
bucket_name = os.getenv("BUCKET_NAME")

async def download_fileobj(key, type):
    # バイナリデータを保持する BytesIO オブジェクトを作成
    if type=="marker":
        marker_mind_data = io.BytesIO()
    else:
        model_glb_data = io.BytesIO()
    try:
        # aioboto3セッションの開始
        async with aioboto3.session.Session().client('s3',
                                                   region_name='nyc3',
                                                   endpoint_url=endpoint_url,
                                                   aws_access_key_id=access_key,
                                                   aws_secret_access_key=secret_key) as client:
            # ファイルオブジェクトをダウンロード
            if type=="marker":
                await client.download_fileobj(bucket_name, f"{key}/marker.mind", marker_mind_data)
                marker_mind_data.seek(0)
                return marker_mind_data
            else:  
                await client.download_fileobj(bucket_name, f"{key}/model.glb", model_glb_data)
                model_glb_data.seek(0)
                return model_glb_data
    except NoCredentialsError:
        print("Credentials not available.")
        return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None