@echo off
echo === RAG API サーバー起動 ===

if not exist venv (
    echo 仮想環境が見つかりません。setup_local.batを実行してください。
    pause
    exit /b 1
)

echo 仮想環境をアクティベート中...
call venv\Scripts\activate.bat

echo サーバーを起動中...
echo http://localhost:8080 でアクセスできます
echo Ctrl+C でサーバーを停止できます

uvicorn app.api.main:app --reload --port 8080