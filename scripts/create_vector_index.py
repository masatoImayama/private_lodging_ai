#!/usr/bin/env python3
"""
Vertex AI Vector Search インデックス作成スクリプト
"""

import os
import sys
from google.cloud import aiplatform
from dotenv import load_dotenv

# .env ファイルを読み込み
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "asia-northeast1")
BUCKET_NAME = os.getenv("BUCKET_NAME")

if not all([PROJECT_ID, BUCKET_NAME]):
    print("エラー: PROJECT_ID と BUCKET_NAME が設定されていません")
    sys.exit(1)

# Vertex AI初期化
aiplatform.init(project=PROJECT_ID, location=LOCATION)

def create_index():
    """Vector Search インデックスを作成"""
    
    print(f"プロジェクト: {PROJECT_ID}")
    print(f"リージョン: {LOCATION}")
    print("Vector Search インデックスを作成中...")
    
    # インデックスの作成
    index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
        display_name="rag_poc_index",
        contents_delta_uri=f"gs://{BUCKET_NAME}/vector_search_temp/",
        dimensions=768,
        approximate_neighbors_count=10,
        distance_measure_type="COSINE_DISTANCE",
        leaf_node_embedding_count=1000,
        leaf_nodes_to_search_percent=10,
        description="RAG PoC用のベクトル検索インデックス",
    )
    
    print(f"インデックス作成中... ID: {index.resource_name}")
    print("作成完了まで数分かかります...")
    
    # 作成完了を待機
    index.wait()
    
    print(f"✓ インデックス作成完了")
    print(f"インデックスID: {index.resource_name.split('/')[-1]}")
    
    return index

def create_endpoint(index):
    """エンドポイントを作成してインデックスをデプロイ"""
    
    print("エンドポイントを作成中...")
    
    # エンドポイントの作成
    endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
        display_name="rag_poc_endpoint",
        description="RAG PoC用のベクトル検索エンドポイント",
        public_endpoint_enabled=True,
    )
    
    print(f"エンドポイント作成中... ID: {endpoint.resource_name}")
    print("作成完了まで数分かかります...")
    
    # エンドポイント作成完了を待機
    endpoint.wait()
    
    print(f"✓ エンドポイント作成完了")
    
    # インデックスをエンドポイントにデプロイ
    print("インデックスをエンドポイントにデプロイ中...")
    
    endpoint.deploy_index(
        index=index,
        deployed_index_id="rag_deployed_index",
        display_name="RAG Deployed Index",
        machine_type="e2-standard-2",
        min_replica_count=1,
        max_replica_count=1,
    )
    
    print("デプロイ完了まで数分かかります...")
    
    print(f"✓ デプロイ完了")
    print(f"エンドポイントID: {endpoint.resource_name.split('/')[-1]}")
    
    return endpoint

def main():
    try:
        # インデックス作成
        index = create_index()
        
        # エンドポイント作成とデプロイ
        endpoint = create_endpoint(index)
        
        # 結果を表示
        index_id = index.resource_name.split('/')[-1]
        endpoint_id = endpoint.resource_name.split('/')[-1]
        
        print("\n" + "="*50)
        print("✓ Vector Search セットアップ完了")
        print("="*50)
        print(f"INDEX_ID={index_id}")
        print(f"INDEX_ENDPOINT_ID={endpoint_id}")
        print("\n以下を.envファイルに追加してください:")
        print(f"INDEX_ID={index_id}")
        print(f"INDEX_ENDPOINT_ID={endpoint_id}")
        
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()