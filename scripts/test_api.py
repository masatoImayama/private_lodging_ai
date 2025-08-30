#!/usr/bin/env python3
"""
RAG API テストスクリプト
"""

import json
import time
import requests
from typing import Dict, Any

# API設定
API_BASE_URL = "http://localhost:8080"
TEST_TENANT_ID = "t_001"
TEST_DOC_ID = "doc-test-001"
TEST_GCS_URI = "gs://proj-rag-poc-bucket/tenants/t_001/raw/sample.pdf"  # 実際のファイルパスに変更

def test_health_check():
    """ヘルスチェックテスト"""
    print("=== ヘルスチェックテスト ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/healthz")
        print(f"ステータス: {response.status_code}")
        print(f"レスポンス: {response.json()}")
        
        if response.status_code == 200:
            print("✓ ヘルスチェック成功")
            return True
        else:
            print("✗ ヘルスチェック失敗")
            return False
            
    except Exception as e:
        print(f"✗ ヘルスチェックエラー: {e}")
        return False

def test_ingest(gcs_uri: str = None):
    """ドキュメント取り込みテスト"""
    print("\n=== ドキュメント取り込みテスト ===")
    
    if not gcs_uri:
        gcs_uri = TEST_GCS_URI
    
    payload = {
        "tenant_id": TEST_TENANT_ID,
        "gcs_uri": gcs_uri,
        "doc_id": TEST_DOC_ID
    }
    
    print(f"リクエスト: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/ingest",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        duration = time.time() - start_time
        
        print(f"ステータス: {response.status_code}")
        print(f"処理時間: {duration:.2f}秒")
        
        if response.status_code == 200:
            result = response.json()
            print(f"レスポンス: {json.dumps(result, indent=2)}")
            print(f"✓ 取り込み成功: {result['chunks']}チャンク作成")
            return True, result
        else:
            print(f"レスポンス: {response.text}")
            print("✗ 取り込み失敗")
            return False, None
            
    except Exception as e:
        print(f"✗ 取り込みエラー: {e}")
        return False, None

def test_chat(query: str = "このドキュメントについて教えて"):
    """チャットテスト"""
    print(f"\n=== チャットテスト: {query} ===")
    
    payload = {
        "tenant_id": TEST_TENANT_ID,
        "query": query,
        "top_k": 10
    }
    
    print(f"リクエスト: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        duration = time.time() - start_time
        
        print(f"ステータス: {response.status_code}")
        print(f"処理時間: {duration:.2f}秒")
        
        if response.status_code == 200:
            result = response.json()
            print(f"レイテンシ: {result['latency_ms']}ms")
            print(f"回答: {result['answer']}")
            print(f"引用数: {len(result['citations'])}")
            
            for i, citation in enumerate(result['citations'], 1):
                print(f"  引用{i}: {citation['doc_id']} p.{citation['page']}")
            
            print("✓ チャット成功")
            return True, result
        else:
            print(f"レスポンス: {response.text}")
            print("✗ チャット失敗")
            return False, None
            
    except Exception as e:
        print(f"✗ チャットエラー: {e}")
        return False, None

def test_tenant_separation():
    """テナント分離テスト"""
    print(f"\n=== テナント分離テスト ===")
    
    # 別テナントでチャットを試行
    payload = {
        "tenant_id": "t_002",  # 異なるテナント
        "query": "先ほど登録したドキュメントについて教えて",
        "top_k": 10
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"ステータス: {response.status_code}")
        
        if response.status_code == 404:
            print("✓ テナント分離成功: 他テナントのドキュメントにアクセス不可")
            return True
        else:
            print("✗ テナント分離失敗: 他テナントのドキュメントにアクセス可能")
            return False
            
    except Exception as e:
        print(f"✗ テナント分離テストエラー: {e}")
        return False

def main():
    print("RAG API テスト開始")
    print(f"API URL: {API_BASE_URL}")
    
    # 1. ヘルスチェック
    if not test_health_check():
        print("APIサーバーが起動していません")
        return
    
    # 2. ドキュメント取り込み
    print("\nGCSにサンプルPDFをアップロードしてから続行してください:")
    print(f"gsutil cp sample.pdf {TEST_GCS_URI}")
    input("準備ができたらEnterキーを押してください...")
    
    ingest_success, ingest_result = test_ingest()
    if not ingest_success:
        print("ドキュメント取り込みが失敗しました")
        return
    
    # 少し待機
    print("インデックス反映のため5秒待機...")
    time.sleep(5)
    
    # 3. チャットテスト
    test_queries = [
        "このドキュメントについて教えて",
        "主要なポイントは何ですか？",
        "手続きはどうすればいいですか？"
    ]
    
    for query in test_queries:
        chat_success, chat_result = test_chat(query)
        if chat_success and chat_result['latency_ms'] > 10000:
            print(f"⚠ 警告: レイテンシが10秒を超過 ({chat_result['latency_ms']}ms)")
    
    # 4. テナント分離テスト
    test_tenant_separation()
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    main()