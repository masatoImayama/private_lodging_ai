# Private Lodging RAG API

GCP（Vertex AI + Vector Search）を使用したRAG（Retrieval-Augmented Generation）APIシステム。PDFドキュメントの取り込みと、テナント別に分離されたチャット機能を提供。

## 機能

- **POST /ingest**: PDFドキュメントの取り込み（抽出・分割・埋め込み・インデックス登録）
- **POST /chat**: テナント別ドキュメントに対するRAGベースの質問応答
- **GET /healthz**: ヘルスチェック

## 必要要件

### GCP設定

1. **プロジェクトと認証**
   - GCPプロジェクトの作成
   - サービスアカウントの作成と認証

2. **API有効化**
   ```bash
   gcloud services enable aiplatform.googleapis.com \
     storage.googleapis.com \
     secretmanager.googleapis.com
   ```

3. **Vertex AI Vector Search**
   - インデックスの作成（768次元、コサイン距離）
   - エンドポイントのデプロイ

### 環境変数

`.env`ファイルを作成し、以下の変数を設定：

```bash
PROJECT_ID=your-gcp-project-id
LOCATION=asia-northeast1
BUCKET_NAME=your-bucket-name
INDEX_ID=your-index-id
INDEX_ENDPOINT_ID=your-index-endpoint-id
```

## セットアップ

### ローカル開発

```bash
# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .envファイルを編集

# アプリケーションの起動
uvicorn app.api.main:app --reload --port 8080
```

### Docker

```bash
# イメージのビルド
docker build -t private-lodging-rag .

# コンテナの実行
docker run -p 8080:8080 --env-file .env private-lodging-rag
```

### Cloud Run デプロイ

```bash
# Cloud Build でイメージをビルド
gcloud builds submit --tag gcr.io/PROJECT_ID/private-lodging-rag

# Cloud Run にデプロイ
gcloud run deploy private-lodging-rag \
  --image gcr.io/PROJECT_ID/private-lodging-rag \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=your-project-id,LOCATION=asia-northeast1,BUCKET_NAME=your-bucket,INDEX_ID=your-index-id,INDEX_ENDPOINT_ID=your-endpoint-id
```

## API使用例

### ドキュメント取り込み

```bash
curl -X POST "http://localhost:8080/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "t_001",
    "gcs_uri": "gs://your-bucket/documents/sample.pdf",
    "doc_id": "doc-2025-001"
  }'
```

### チャット

```bash
curl -X POST "http://localhost:8080/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "t_001",
    "query": "手続きについて教えて",
    "top_k": 15
  }'
```

## アーキテクチャ

```
/app
  /api
    main.py            # FastAPI アプリケーション
  /rag
    indexer.py         # ドキュメント処理・インデックス登録
    retriever.py       # ベクター検索・結果フィルタリング
    generator.py       # 回答生成・引用管理
  /schemas
    dto.py             # Pydantic データモデル
  /utils
    pdf.py             # PDF抽出
    chunks.py          # テキスト分割
    hash.py            # チェックサム計算
  config.py           # 設定管理
```

## テナント分離

- ベクター検索は`namespace=tenant_id`で分離
- 各テナントは自身のドキュメントのみアクセス可能
- クロステナントでのデータ漏洩を防止

## 引用システム

- 回答には必ず引用を含む
- 各引用にはdoc_id、ページ番号、GCSパス、chunk_id、checksumを含む
- 引用がない場合は409エラーを返す

## パフォーマンス要件

- `/chat`エンドポイントは10秒以内で応答
- MMRアルゴリズムによる結果の多様化
- 効率的なベクター検索とキャッシュ