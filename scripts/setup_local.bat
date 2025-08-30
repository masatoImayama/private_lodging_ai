@echo off
echo === ローカル環境セットアップ ===

echo Python仮想環境を作成中...
python -m venv venv

echo 仮想環境をアクティベート中...
call venv\Scripts\activate.bat

echo 依存関係をインストール中...
pip install -r requirements.txt

echo セットアップ完了！

echo 次のコマンドでアプリケーションを起動してください:
echo call venv\Scripts\activate.bat
echo uvicorn app.api.main:app --reload --port 8080

pause