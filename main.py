import subprocess
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
import io
import src.download_assets as da
import src.upload_assets as ua
from fastapi.responses import FileResponse, StreamingResponse
from typing import List

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
    marker_file = io.BytesIO(marker_content)  # バイト列からファイルオブジェクトに変換
    model_file = io.BytesIO(model_content)    # バイト列からファイルオブジェクトに変換
    
    # 一意なkeyを発行
    unique_key = uuid.uuid4()
    
    # DBにアップロード
    for content, path in [(marker_file, "marker.mind"), (model_file, "model.glb")]:
        try:
            await ua.upload_fileobj(content, f"{str(unique_key)}/{path}")
            subprocess.run(
                ["s3cmd", "setacl", f"s3://custom-ar-assets/{str(unique_key)}/{path}", "--acl-public"],
                check=True
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

    
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
    subprocess.run(["s3cmd", "setacl", f"s3://custom-ar-assets/{str(unique_key)}/marker.mind", "--acl-public"])

    # 各modelファイルをアップロード
    for i, model in enumerate(models):
        model_content = await model.read()
        model_file = io.BytesIO(model_content)
        await ua.upload_fileobj(model_file, f"{str(unique_key)}/model_{i}.glb")
        subprocess.run(["s3cmd", "setacl", f"s3://custom-ar-assets/{str(unique_key)}/model_{i}.glb", "--acl-public"])

    return unique_key

@app.get("/marker/{key}")
async def download_marker(key: str):
    marker_mind_data = await da.download_fileobj(key, "marker")
    if marker_mind_data is None:
        raise HTTPException(status_code=404, detail="Marker not found or download error")
    return StreamingResponse(marker_mind_data, media_type="application/octet-stream")

@app.get("/model/{key}")
async def download_marker(key: str):
    model_glb_data = await da.download_fileobj(key, "model")
    if model_glb_data is None:
        raise HTTPException(status_code=404, detail="Model not found or download error")
    return StreamingResponse(model_glb_data, media_type="application/octet-stream")
