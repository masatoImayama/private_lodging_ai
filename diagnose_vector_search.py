"""
Vector Search 包括的診断スクリプト
全ての可能性を体系的にテストする
"""
import os
from google.cloud import aiplatform
from google.cloud import aiplatform_v1
from google.auth import default
import google.auth.transport.requests

def diagnose_vector_search():
    """Vector Search の全ての側面を診断"""

    # 設定値
    PROJECT_ID = "private-lodging-ai"
    PROJECT_NUMBER = "863645902320"
    LOCATION = "us-central1"
    INDEX_ID = "6734414162128011264"

    print("=== Vector Search 包括的診断 ===\n")

    # 1. 認証状況の確認
    print("1. 認証状況の確認")
    try:
        credentials, project = default()
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        print(f"   [OK] 認証成功: {project}")
        print(f"   [OK] トークン有効: {credentials.valid}")
        print(f"   [OK] サービスアカウント: {getattr(credentials, 'service_account_email', 'N/A')}")
    except Exception as e:
        print(f"   [ERROR] 認証エラー: {e}")
        return False

    # 2. 高レベルAPI接続テスト
    print("\n2. 高レベルAPI (aiplatform) 接続テスト")
    try:
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        print("   [OK] aiplatform.init() 成功")

        # Index取得テスト
        index = aiplatform.MatchingEngineIndex(
            index_name=f"projects/{PROJECT_NUMBER}/locations/{LOCATION}/indexes/{INDEX_ID}"
        )
        print(f"   [OK] Index取得成功: {index.display_name}")

    except Exception as e:
        print(f"   [ERROR] 高レベルAPIエラー: {e}")

    # 3. 低レベルAPI接続テスト
    print("\n3. 低レベルAPI (aiplatform_v1) 接続テスト")
    try:
        # リージョンを指定してクライアントを作成
        client_options = {"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"}
        client = aiplatform_v1.IndexServiceClient(client_options=client_options)
        index_name = f"projects/{PROJECT_NUMBER}/locations/{LOCATION}/indexes/{INDEX_ID}"

        # 単純な情報取得テスト（upsertではない）
        request = aiplatform_v1.GetIndexRequest(name=index_name)
        response = client.get_index(request=request)
        print(f"   [OK] Index情報取得成功: {response.display_name}")
        print(f"   [OK] Update Method: {response.index_update_method}")
        print(f"   [OK] Deployed Indexes: {len(response.deployed_indexes)}")

    except Exception as e:
        print(f"   [ERROR] 低レベルAPIエラー: {e}")
        return False

    # 4. 権限テスト（実際のupsert前のdry-run的なテスト）
    print("\n4. 権限テスト")
    try:
        # 空のdatapointでテスト
        test_datapoint = aiplatform_v1.IndexDatapoint(
            datapoint_id="test_permission",
            feature_vector=[0.1] * 768  # 768次元のテストベクトル
        )

        request = aiplatform_v1.UpsertDatapointsRequest(
            index=index_name,
            datapoints=[test_datapoint]
        )

        # 実際のupsert実行
        response = client.upsert_datapoints(request=request)
        print(f"   [OK] テストupsert成功: {response}")

        # テストデータを削除
        delete_request = aiplatform_v1.RemoveDatapointsRequest(
            index=index_name,
            datapoint_ids=["test_permission"]
        )
        client.remove_datapoints(delete_request)
        print("   [OK] テストデータ削除完了")

        return True

    except Exception as e:
        print(f"   [ERROR] 権限テストエラー: {e}")
        print(f"   エラータイプ: {type(e).__name__}")

        # 詳細なエラー分析
        if "not found or is not active" in str(e):
            print("   [INFO] Indexが見つからないか非アクティブ")
            print("   [INFO] 原因: Index初期化未完了 または 権限不足")
        elif "permission" in str(e).lower():
            print("   [INFO] 権限不足")
            print("   [INFO] 必要な権限: roles/aiplatform.admin または roles/aiplatform.user")
        elif "authentication" in str(e).lower():
            print("   [INFO] 認証エラー")

        return False

if __name__ == "__main__":
    success = diagnose_vector_search()
    if success:
        print("\n[SUCCESS] 全ての診断テストが成功しました")
        print("Vector Search upsert操作が正常に動作するはずです")
    else:
        print("\n[FAILED] 診断で問題が発見されました")
        print("上記のエラー情報を確認して問題を解決してください")