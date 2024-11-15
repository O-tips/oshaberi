from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
import io, os
import src.download_assets as da
import src.upload_assets as ua
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
from dotenv import load_dotenv
import aioboto3
import asyncio
from botocore.exceptions import ClientError
from io import BytesIO
import zipfile

# .envファイルの読み込み
load_dotenv()

# 環境変数の取得
endpoint_url = os.getenv("ENDPOINT_URL")
access_key = os.getenv("ACCESS_KEY")
secret_key = os.getenv("SECRET_KEY")
bucket_name = os.getenv("BUCKET_NAME")
endpoint_url_for_download_multi_files = os.getenv("ENDPOINT_URL_FOR_DOWNLOAD_MULTI_FILES")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 許可するオリジン（*は全てのオリジンを許可）
    allow_credentials=True,
    allow_methods=["*"],  # 許可するHTTPメソッド
    allow_headers=["*"],  # 許可するヘッダー
)

@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}

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
    
    #keyを返却
    return unique_key

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

    # 各modelファイルをアップロード
    for i, model in enumerate(models):
        model_content = await model.read()
        model_file = io.BytesIO(model_content)
        # `model_i.glb`という形式でファイルを保存
        await ua.upload_fileobj(model_file, f"{str(unique_key)}/model_{i}.glb")

    # 一意なkeyを返却
    return unique_key

@app.get("/marker/{key}")
async def download_marker(key: str):
    marker_mind_data = await da.download_fileobj(key, "marker")
    # ダウンロードに失敗した場合
    if marker_mind_data is None:
        raise HTTPException(status_code=404, detail="Marker not found or download error")
    return StreamingResponse(marker_mind_data, media_type="application/octet-stream")

@app.get("/model/{key}")
async def download_marker(key: str):
    model_glb_data = await da.download_fileobj(key, "model")
    # ダウンロードに失敗した場合
    if model_glb_data is None:
        raise HTTPException(status_code=404, detail="Model not found or download error")
    return StreamingResponse(model_glb_data, media_type="application/octet-stream")

@app.get("/model_list/{key}")
async def download_models(key: str):
    zip_buffer = BytesIO()
    async with aioboto3.session.Session().client('s3',
                          region_name='nyc3',
                          endpoint_url=endpoint_url_for_download_multi_files,
                          aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key) as client:
        try:
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                result = await client.list_objects_v2(Bucket=bucket_name, Prefix=f"custom-ar-assets/{key}/")
                if 'Contents' in result:
                    for obj in result['Contents']:
                        model_glb_data = io.BytesIO()
                        # 対象の拡張子のファイルのみフィルタリング
                        if obj['Key'].endswith(".glb" or ".gltf" or ".obj" or ".fbx"):
                            print(obj['Key'])
                            # ファイルをダウンロード
                            await client.download_fileobj(bucket_name, obj['Key'], model_glb_data)
                            zip_file.writestr(obj['Key'], model_glb_data.read())
                            model_glb_data.seek(0)
                else:
                    print("ディレクトリ内にファイルはありません")
        except ClientError as e:
            # 404エラーが返された場合は、オブジェクトが存在しないことを示す
            if e.response['Error']['Code'] == '404':
                print(f"オブジェクト '{key}' は存在しません")
            else:
                # 他のエラーが発生した場合
                print(f"エラー: {e}")
    zip_buffer.seek(0)
    return StreamingResponse(zip_buffer, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=models.zip"})