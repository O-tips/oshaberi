from fastapi import FastAPI, UploadFile, File, HTTPException
import uuid
import io
import src.download_assets as da
import src.upload_assets as ua

app = FastAPI()

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
        await ua.upload_fileobj(content, f"{unique_key}/{path}")
    
    #keyを返却
    return unique_key