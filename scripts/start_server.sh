#!/bin/bash

echo "=== RAG API サーバー起動 ==="

if [ ! -d "venv" ]; then
    echo "仮想環境が見つかりません。setup_local.shを実行してください。"
    exit 1
fi

echo "仮想環境をアクティベート中..."
source venv/bin/activate

echo "サーバーを起動中..."
echo "http://localhost:8080 でアクセスできます"
echo "Ctrl+C でサーバーを停止できます"

uvicorn app.api.main:app --reload --port 8080