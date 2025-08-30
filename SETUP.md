# セットアップ手順

## 1. .envファイルの設定 ✓

`.env`ファイルが作成されています。実際のGCPプロジェクト情報に更新してください：

```bash
PROJECT_ID=あなたのGCPプロジェクトID
LOCATION=asia-northeast1
BUCKET_NAME=あなたのバケット名
INDEX_ID=作成したインデックスID
INDEX_ENDPOINT_ID=作成したエンドポイントID
```

## 2. GCP Vector Searchインデックスの準備

### 2-1. 基本的なGCP設定

```bash
# スクリプトを実行してGCP環境を準備
./scripts/setup_gcp.sh
```

これにより以下が実行されます：
- 必要なAPIの有効化
- GCSバケットの作成
- サービスアカウントの作成と権限設定

### 2-2. Vector Searchインデックスの作成

**方法1: Pythonスクリプト（推奨）**

```bash
# 自動でインデックスとエンドポイントを作成
python scripts/create_vector_index.py
```

**方法2: 手動作成**

1. [Vertex AI Console](https://console.cloud.google.com/vertex-ai/matching-engine/indexes)にアクセス
2. インデックスを作成：
   - 名前: `rag_poc_index`
   - ディメンション: `768`
   - 距離測定: コサイン類似度
   - アルゴリズム: Tree-AH
3. エンドポイントを作成してインデックスをデプロイ

### 2-3. .envファイルの更新

作成されたIDを`.env`ファイルに設定：

```bash
INDEX_ID=作成されたインデックスのID
INDEX_ENDPOINT_ID=作成されたエンドポイントのID
```

## 3. ローカルテスト環境のセットアップ

### Windows

```cmd
# 環境セットアップ
scripts\setup_local.bat

# サーバー起動
scripts\start_server.bat
```

### Linux/macOS

```bash
# 環境セットアップ
./scripts/setup_local.sh

# サーバー起動
./scripts/start_server.sh
```

### 手動セットアップ

```bash
# Python仮想環境作成
python -m venv venv

# 仮想環境アクティベート (Windows)
venv\Scripts\activate.bat

# 仮想環境アクティベート (Linux/macOS)
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# サーバー起動
uvicorn app.api.main:app --reload --port 8080
```

## 4. テスト実行

### 4-1. テスト用PDFの準備

```bash
# サンプルPDFをGCSにアップロード
gsutil cp sample.pdf gs://あなたのバケット名/tenants/t_001/raw/
```

### 4-2. 自動テスト実行

```bash
# APIテストスクリプト実行
python scripts/test_api.py
```

### 4-3. 手動テスト

サーバーが起動したら `http://localhost:8080/docs` でSwagger UIにアクセスできます。

**ヘルスチェック:**
```bash
curl http://localhost:8080/healthz
```

**ドキュメント取り込み:**
```bash
curl -X POST "http://localhost:8080/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "t_001",
    "gcs_uri": "gs://バケット名/tenants/t_001/raw/sample.pdf",
    "doc_id": "doc-test-001"
  }'
```

**チャット:**
```bash
curl -X POST "http://localhost:8080/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "t_001",
    "query": "このドキュメントについて教えて",
    "top_k": 15
  }'
```

## トラブルシューティング

### よくある問題

1. **`INDEX_ID` または `INDEX_ENDPOINT_ID` が見つからない**
   - Vector Searchコンソールでインデックス/エンドポイントIDを確認
   - `.env`ファイルに正しいIDが設定されているか確認

2. **GCS権限エラー**
   - サービスアカウントに適切な権限が設定されているか確認
   - `gcloud auth application-default login` を実行

3. **PDFファイルが見つからない**
   - GCSにファイルが正しくアップロードされているか確認
   - バケット名とパスが正しいか確認

4. **Vector Searchエラー**
   - インデックスが正しくデプロイされているか確認
   - インデックスの作成が完了しているか確認（数分かかる場合があります）

### ログの確認

```bash
# サーバーログを確認
uvicorn app.api.main:app --reload --port 8080 --log-level debug
```