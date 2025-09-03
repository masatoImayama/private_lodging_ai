import requests
import json
import time

API_BASE_URL = "http://localhost:8080"

def test_ingest(tenant_id, gcs_uri, doc_id):
    """PDFをインジェストする"""
    url = f"{API_BASE_URL}/ingest"
    payload = {
        "tenant_id": tenant_id,
        "gcs_uri": gcs_uri,
        "doc_id": doc_id
    }
    
    print(f"\n📥 Ingesting for {tenant_id}...")
    print(f"   Document: {doc_id}")
    print(f"   GCS URI: {gcs_uri}")
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Success: {result[\"chunks\"]} chunks created")
        print(f"   Job ID: {result[\"job_id\"]}")
        return result
    else:
        print(f"   ❌ Failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def test_chat(tenant_id, query):
    """チャットAPIをテスト"""
    url = f"{API_BASE_URL}/chat"
    payload = {
        "tenant_id": tenant_id,
        "query": query,
        "top_k": 10
    }
    
    print(f"\n💬 Chat test for {tenant_id}")
    print(f"   Query: {query}")
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Answer received (latency: {result.get(\"latency_ms\", 0)}ms)")
        print(f"   Answer: {result[\"answer\"][:200]}...")
        print(f"   Citations: {len(result.get(\"citations\", []))} sources")
        
        if result.get("citations"):
            print("   Citation documents:")
            doc_ids = set()
            for citation in result["citations"]:
                doc_ids.add(citation["doc_id"])
            for doc_id in doc_ids:
                print(f"      - {doc_id}")
        
        return result
    else:
        print(f"   ❌ Failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def main():
    print("=" * 60)
    print("🔬 TENANT ISOLATION TEST FOR VECTOR SEARCH")
    print("=" * 60)
    
    print("\n[STEP 1] Ingesting PDFs for each tenant...")
    
    # テナント001のPDFをインジェスト
    result1 = test_ingest(
        tenant_id="t_001",
        gcs_uri="gs://private-lodging-ai-rag-poc/test-pdfs/tenant_001_manual.pdf",
        doc_id="manual-2025-001"
    )
    
    # 少し待つ
    time.sleep(2)
    
    # テナント002のPDFをインジェスト
    result2 = test_ingest(
        tenant_id="t_002",
        gcs_uri="gs://private-lodging-ai-rag-poc/test-pdfs/tenant_002_products.pdf",
        doc_id="catalog-2025-002"
    )
    
    if not result1 or not result2:
        print("\n❌ Ingest failed. Stopping test.")
        return
    
    print("\n" + "=" * 60)
    print("[STEP 2] Testing tenant-specific queries...")
    print("=" * 60)
    
    # テナント001特有の質問（社内システム関連）
    print("\n🔍 Test 1: Query t_001 about internal systems")
    chat1 = test_chat(
        tenant_id="t_001",
        query="ログイン手順を教えてください"
    )
    
    time.sleep(2)
    
    # テナント002特有の質問（製品カタログ関連）
    print("\n🔍 Test 2: Query t_002 about products")
    chat2 = test_chat(
        tenant_id="t_002",
        query="ProServer X500の仕様を教えてください"
    )
    
    time.sleep(2)
    
    print("\n" + "=" * 60)
    print("[STEP 3] CROSS-TENANT ISOLATION TEST")
    print("=" * 60)
    
    # テナント001でテナント002の情報を検索（見つからないはず）
    print("\n⚠️  Test 3: Query t_001 for t_002 content (should NOT find)")
    chat3 = test_chat(
        tenant_id="t_001",
        query="ProServer X500やCloudStorage Proについて教えてください"
    )
    
    time.sleep(2)
    
    # テナント002でテナント001の情報を検索（見つからないはず）
    print("\n⚠️  Test 4: Query t_002 for t_001 content (should NOT find)")
    chat4 = test_chat(
        tenant_id="t_002",
        query="勤怠管理システムや経費精算の手順を教えてください"
    )
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    # 結果の検証
    isolation_ok = True
    
    # Test 1の検証
    if chat1 and chat1.get("citations"):
        docs = [c["doc_id"] for c in chat1["citations"]]
        if any("manual" in d for d in docs):
            print("✅ Test 1: t_001 found its own data correctly")
        else:
            print("❌ Test 1: t_001 did not find expected data")
            isolation_ok = False
    
    # Test 2の検証
    if chat2 and chat2.get("citations"):
        docs = [c["doc_id"] for c in chat2["citations"]]
        if any("catalog" in d for d in docs):
            print("✅ Test 2: t_002 found its own data correctly")
        else:
            print("❌ Test 2: t_002 did not find expected data")
            isolation_ok = False
    
    # Test 3の検証（t_001でt_002のデータが見つからないこと）
    if chat3:
        if not chat3.get("citations") or not any("catalog" in c["doc_id"] for c in chat3.get("citations", [])):
            print("✅ Test 3: t_001 correctly isolated from t_002 data")
        else:
            print("❌ Test 3: t_001 found t_002 data (ISOLATION BREACH!)")
            isolation_ok = False
    
    # Test 4の検証（t_002でt_001のデータが見つからないこと）
    if chat4:
        if not chat4.get("citations") or not any("manual" in c["doc_id"] for c in chat4.get("citations", [])):
            print("✅ Test 4: t_002 correctly isolated from t_001 data")
        else:
            print("❌ Test 4: t_002 found t_001 data (ISOLATION BREACH!)")
            isolation_ok = False
    
    print("\n" + "=" * 60)
    if isolation_ok:
        print("🎉 TENANT ISOLATION: WORKING CORRECTLY")
    else:
        print("⚠️  TENANT ISOLATION: FAILED")
    print("=" * 60)

if __name__ == "__main__":
    main()
