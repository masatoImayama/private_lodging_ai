#!/bin/bash

echo "=== ローカル環境セットアップ ==="

# Python仮想環境の作成
echo "Python仮想環境を作成中..."
python3 -m venv venv

# 仮想環境のアクティベート
echo "仮想環境をアクティベート中..."
source venv/bin/activate

# 依存関係のインストール
echo "依存関係をインストール中..."
pip install -r requirements.txt

echo "セットアップ完了！"
echo ""
echo "次のコマンドでアプリケーションを起動してください:"
echo "source venv/bin/activate"
echo "uvicorn app.api.main:app --reload --port 8080"