import subprocess
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
import io
import src.download_assets as da
import src.upload_assets as ua
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
import os

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

@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}

async def run_s3cmd(command: List[str]):
    """非同期でs3cmdを実行"""
    # 環境変数を辞書として設定
    env = os.environ.copy()
    env['AWS_ACCESS_KEY_ID'] = access_key
    env['AWS_SECRET_ACCESS_KEY'] = secret_key
    env['AWS_DEFAULT_REGION'] = 'nyc3'  # 適切な地域に設定
    env['S3_BUCKET_NAME'] = bucket_name
    env['S3_ENDPOINT_URL'] = endpoint_url

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env  # 環境変数を辞書として渡す
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise HTTPException(status_code=500, detail=f"s3cmd failed: {stderr.decode()}")
    return stdout.decode()

@app.post("/upload")
async def upload_marker_and_model(marker:UploadFile = File(...), model:UploadFile = File(...)) -> uuid.UUID:
    # ファイルの拡張子をチェック
    if not marker.filename.endswith(".mind"):
        raise HTTPException(status_code=400, detail="Marker file must have .mind extension")
    # メモリから直接S3にアップロード
    marker_content = await marker.read()
    model_content = await model.read()
    # marker_contentとmodel_contentをBytesIOに変換
    marker_file = io.BytesIO(marker_content)  # バイト列からファイルオブジェクトに変換
    model_file = io.BytesIO(model_content)    # バイト列からファイルオブジェクトに変換
    #一意なkeyを発行
    unique_key = uuid.uuid4()
    #dbにアップロード
    for content, path in [(marker_file, "marker.mind"),(model_file, "model.glb")]:
        await ua.upload_fileobj(content, f"{str(unique_key)}/{path}")
        await run_s3cmd([
            "s3cmd", "--debug", "setacl", f"s3://custom-ar-assets/{str(unique_key)}/{path}", "--acl-public"
        ])
    
    #keyを返却
    return unique_key

# @app.post("/upload")
# async def upload_marker_and_model(marker: UploadFile = File(...), model: UploadFile = File(...)) -> uuid.UUID:
#     # ファイルの拡張子をチェック
#     if not marker.filename.endswith(".mind"):
#         raise HTTPException(status_code=400, detail="Marker file must have .mind extension")
    
#     # メモリから直接S3にアップロード
#     marker_content = await marker.read()
#     model_content = await model.read()
#     marker_file = io.BytesIO(marker_content)  # バイト列からファイルオブジェクトに変換
#     model_file = io.BytesIO(model_content)    # バイト列からファイルオブジェクトに変換
    
#     # 一意なkeyを発行
#     unique_key = uuid.uuid4()
    
#     # DBにアップロード
#     for content, path in [(marker_file, "marker.mind"), (model_file, "model.glb")]:
#         try:
#             # ファイルアップロード処理
#             await ua.upload_fileobj(content, f"{str(unique_key)}/{path}")
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

#     for content, path in [(marker_file, "marker.mind"), (model_file, "model.glb")]:
#         try:
#             # アップロード成功後にs3cmdでsetaclを実行
#             await run_s3cmd([
#                 "s3cmd", "--debug", "setacl", f"s3://custom-ar-assets/{str(unique_key)}/{path}", "--acl-public"
#             ])
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

#     return unique_key

@app.post("/upload-list")
async def upload_marker_and_models(marker: UploadFile = File(...), models: List[UploadFile] = File(...)) -> uuid.UUID:
    # ファイルの拡張子をチェック
    if not marker.filename.endswith(".mind"):
        raise HTTPException(status_code=400, detail="Marker file must have .mind extension")
    
    # メモリから直接S3にアップロード
    marker_content = await marker.read()
    marker_file = io.BytesIO(marker_content)  # バイト列からファイルオブジェクトに変換
    
    # 一意なkeyを発行
    unique_key = uuid.uuid4()

    # markerファイルをアップロード
    await ua.upload_fileobj(marker_file, f"{str(unique_key)}/marker.mind")
    await run_s3cmd([
        "s3cmd", "--debug", "setacl", f"s3://custom-ar-assets/{str(unique_key)}/marker.mind", "--acl-public"
    ])

    # 各modelファイルをアップロード
    for i, model in enumerate(models):
        model_content = await model.read()
        model_file = io.BytesIO(model_content)
        await ua.upload_fileobj(model_file, f"{str(unique_key)}/model_{i}.glb")
        await run_s3cmd([
            "s3cmd", "setacl", f"s3://custom-ar-assets/{str(unique_key)}/model_{i}.glb", "--acl-public"
        ])

    return unique_key

@app.get("/marker/{key}")
async def download_marker(key: str):
    marker_mind_data = await da.download_fileobj(key, "marker")
    if marker_mind_data is None:
        raise HTTPException(status_code=404, detail="Marker not found or download error")
    return StreamingResponse(marker_mind_data, media_type="application/octet-stream")

@app.get("/model/{key}")
async def download_model(key: str):
    model_glb_data = await da.download_fileobj(key, "model")
    if model_glb_data is None:
        raise HTTPException(status_code=404, detail="Model not found or download error")
    return StreamingResponse(model_glb_data, media_type="application/octet-stream")
