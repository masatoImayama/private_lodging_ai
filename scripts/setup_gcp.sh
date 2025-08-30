#!/bin/bash

# GCP Vector Search インデックス準備スクリプト
# 使用前に以下の変数を実際の値に更新してください

set -e

# 環境変数の読み込み
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 必要な変数が設定されているかチェック
if [ -z "$PROJECT_ID" ] || [ -z "$LOCATION" ] || [ -z "$BUCKET_NAME" ]; then
    echo "エラー: PROJECT_ID, LOCATION, BUCKET_NAMEが設定されていません"
    echo ".envファイルを確認してください"
    exit 1
fi

echo "=== GCP RAG PoC セットアップ開始 ==="
echo "プロジェクトID: $PROJECT_ID"
echo "リージョン: $LOCATION"
echo "バケット名: $BUCKET_NAME"

# 1. gcloud設定確認
echo "=== gcloud設定確認 ==="
gcloud config set project $PROJECT_ID
gcloud auth application-default login

# 2. 必要なAPIの有効化
echo "=== 必要なAPIの有効化 ==="
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

echo "API有効化完了。数分待ってから次の手順を実行してください。"

# 3. GCSバケットの作成
echo "=== GCSバケットの作成 ==="
if gsutil ls gs://$BUCKET_NAME 2>/dev/null; then
    echo "バケット $BUCKET_NAME は既に存在します"
else
    gsutil mb -l $LOCATION gs://$BUCKET_NAME
    echo "バケット $BUCKET_NAME を作成しました"
fi

# バケット構造の作成
gsutil -m mkdir -p gs://$BUCKET_NAME/tenants/t_001/raw/
gsutil -m mkdir -p gs://$BUCKET_NAME/tenants/t_001/index/
gsutil -m mkdir -p gs://$BUCKET_NAME/tenants/t_002/raw/
gsutil -m mkdir -p gs://$BUCKET_NAME/tenants/t_002/index/

echo "バケット構造を作成しました"

# 4. サービスアカウントの作成と権限設定
echo "=== サービスアカウントの作成 ==="
SA_NAME="sa-rag-api"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# サービスアカウントが既に存在するかチェック
if gcloud iam service-accounts describe $SA_EMAIL 2>/dev/null; then
    echo "サービスアカウント $SA_EMAIL は既に存在します"
else
    gcloud iam service-accounts create $SA_NAME \
        --display-name="RAG API Service Account"
    echo "サービスアカウント $SA_EMAIL を作成しました"
fi

# 権限の付与
echo "=== 権限の付与 ==="
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor"

echo "権限設定完了"

echo "=== 手動作業が必要な項目 ==="
echo "以下の作業をGCPコンソールで手動で行ってください："
echo ""
echo "1. Vertex AI Vector Search インデックスの作成："
echo "   - https://console.cloud.google.com/vertex-ai/matching-engine/indexes"
echo "   - インデックス名: rag_poc_index"
echo "   - ディメンション: 768"
echo "   - 距離測定: コサイン類似度"
echo "   - アルゴリズム: Tree-AH"
echo ""
echo "2. インデックスエンドポイントの作成とデプロイ："
echo "   - エンドポイント名: rag_poc_endpoint"
echo "   - 上記で作成したインデックスをデプロイ"
echo ""
echo "3. 作成されたIDを.envファイルに設定："
echo "   - INDEX_ID=<作成されたインデックスのID>"
echo "   - INDEX_ENDPOINT_ID=<作成されたエンドポイントのID>"
echo ""
echo "4. テスト用PDFファイルのアップロード："
echo "   gsutil cp /path/to/sample.pdf gs://$BUCKET_NAME/tenants/t_001/raw/"
echo ""
echo "=== セットアップ完了 ==="