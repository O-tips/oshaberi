import subprocess
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
import io
from fastapi.responses import StreamingResponse
from typing import List
import os
from boto3.session import Session

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 許可するオリジン（*は全てのオリジンを許可）
    allow_credentials=True,
    allow_methods=["*"],  # 許可するHTTPメソッド
    allow_headers=["*"],  # 許可するヘッダー
)

# 環境変数の取得
access_key = os.getenv('ACCESS_KEY')
secret_key = os.getenv('SECRET_KEY')
bucket_name = os.getenv('BUCKET_NAME')
endpoint_url = os.getenv('ENDPOINT_URL')
region_name = "nyc3"  # 適切な地域を指定

def upload_file_and_make_it_public(filename: str, file_obj: io.BytesIO, bucket: str):
    """ファイルをアップロードし、パブリックアクセス可能にする"""
    session = Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region_name,
    )
    client = session.client(
        "s3", endpoint_url=endpoint_url, region_name=region_name,
    )
    # ファイルをアップロード
    client.upload_fileobj(Fileobj=file_obj, Bucket=bucket, Key=filename)
    # アクセス権限を公開に設定
    resource = session.resource(
        "s3", endpoint_url=endpoint_url, region_name=region_name,
    )
    resource.Object(bucket, filename).Acl().put(ACL='public-read')

@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}

@app.post("/upload")
async def upload_marker_and_model(marker: UploadFile = File(...), model: UploadFile = File(...)) -> uuid.UUID:
    # ファイルの拡張子をチェック
    if not marker.filename.endswith(".mind"):
        raise HTTPException(status_code=400, detail="Marker file must have .mind extension")
    
    # メモリから直接ファイルオブジェクトを作成
    marker_content = await marker.read()
    model_content = await model.read()
    marker_file = io.BytesIO(marker_content)
    model_file = io.BytesIO(model_content)

    # 一意なキーを作成
    unique_key = uuid.uuid4()
    marker_path = f"{unique_key}/marker.mind"
    model_path = f"{unique_key}/model.glb"

    # ファイルをアップロードし、公開設定
    try:
        upload_file_and_make_it_public(marker_path, marker_file, bucket_name)
        upload_file_and_make_it_public(model_path, model_file, bucket_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading files: {str(e)}")

    # 成功した場合は一意なキーを返却
    return unique_key

@app.post("/upload-list")
async def upload_marker_and_models(marker: UploadFile = File(...), models: List[UploadFile] = File(...)) -> uuid.UUID:
    # ファイルの拡張子をチェック
    if not marker.filename.endswith(".mind"):
        raise HTTPException(status_code=400, detail="Marker file must have .mind extension")
    
    # 一意なキーを作成
    unique_key = uuid.uuid4()
    marker_path = f"{unique_key}/marker.mind"

    # Markerファイルをアップロードし、公開設定
    marker_content = await marker.read()
    marker_file = io.BytesIO(marker_content)
    try:
        upload_file_and_make_it_public(marker_path, marker_file, bucket_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading marker: {str(e)}")

    # 各Modelファイルをアップロード
    for i, model in enumerate(models):
        model_content = await model.read()
        model_file = io.BytesIO(model_content)
        model_path = f"{unique_key}/model_{i}.glb"
        try:
            upload_file_and_make_it_public(model_path, model_file, bucket_name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error uploading model_{i}: {str(e)}")

    return unique_key

@app.get("/marker/{key}")
async def download_marker(key: str):
    """Markerファイルをダウンロード"""
    # ロジックを実装する
    raise NotImplementedError("Download functionality not implemented")

@app.get("/model/{key}")
async def download_model(key: str):
    """Modelファイルをダウンロード"""
    # ロジックを実装する
    raise NotImplementedError("Download functionality not implemented")
