from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
import io
import src.download_assets as da
import src.upload_assets as ua
from fastapi.responses import FileResponse, StreamingResponse


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