# ベースイメージとしてPythonを使用
FROM python:3.10-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# FastAPIアプリケーションコードをコピー
COPY . .

# .s3cfgをコンテナにコピー
COPY .s3cfg .  

# ポートを公開
EXPOSE 8000

# FastAPIアプリケーションを起動するコマンド
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
