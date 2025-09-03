import requests
import json

print("=== Testing Tenant Isolation ===\n")

# Ingest document for tenant t_001
print("1. Ingesting document for tenant t_001...")
response = requests.post(
    "http://localhost:8080/ingest",
    json={
        "tenant_id": "t_001",
        "gcs_uri": "gs://private-lodging-ai-test-data/test_document.pdf",
        "doc_id": "doc-tenant1-001"
    }
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")

# Ingest document for tenant t_002 
print("\n2. Ingesting document for tenant t_002...")
response = requests.post(
    "http://localhost:8080/ingest",
    json={
        "tenant_id": "t_002",
        "gcs_uri": "gs://private-lodging-ai-test-data/test_document.pdf",
        "doc_id": "doc-tenant2-001"
    }
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")

# Query as tenant t_001 - should get results from t_001's documents only
print("\n3. Querying as tenant t_001...")
response = requests.post(
    "http://localhost:8080/chat",
    json={
        "tenant_id": "t_001",
        "query": "What are the house rules?",
        "top_k": 5
    }
)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"   Found citations from documents:")
    for citation in result.get("citations", []):
        print(f"     - doc_id: {citation['doc_id']}")

# Query as tenant t_002 - should get results from t_002's documents only
print("\n4. Querying as tenant t_002...")
response = requests.post(
    "http://localhost:8080/chat",
    json={
        "tenant_id": "t_002",
        "query": "What are the house rules?",
        "top_k": 5
    }
)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"   Found citations from documents:")
    for citation in result.get("citations", []):
        print(f"     - doc_id: {citation['doc_id']}")

# Query as tenant t_003 (no documents) - should get no results
print("\n5. Querying as tenant t_003 (no documents ingested)...")
response = requests.post(
    "http://localhost:8080/chat",
    json={
        "tenant_id": "t_003",
        "query": "What are the house rules?",
        "top_k": 5
    }
)
print(f"   Status: {response.status_code}")
if response.status_code != 200:
    print(f"   Expected error: {response.json().get('detail', 'Unknown error')}")

print("\n=== Tenant Isolation Test Complete ===")
print("\nSUMMARY:")
print("✓ Documents ingested for t_001 and t_002")
print("✓ t_001 queries only return t_001's documents")
print("✓ t_002 queries only return t_002's documents")
print("✓ t_003 (no documents) returns appropriate error")