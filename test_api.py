import requests
import json

# Test ingestion first
print("Testing /ingest endpoint...")
ingest_response = requests.post(
    "http://localhost:8080/ingest",
    json={
        "tenant_id": "t_001",
        "gcs_uri": "gs://private-lodging-ai-test-data/test_document.pdf",
        "doc_id": "doc-test-001"
    }
)
print(f"Ingest status: {ingest_response.status_code}")
print(f"Ingest response: {json.dumps(ingest_response.json(), indent=2)}")

# Test chat
print("\nTesting /chat endpoint...")
chat_response = requests.post(
    "http://localhost:8080/chat",
    json={
        "tenant_id": "t_001",
        "query": "What is the check-in process?",
        "top_k": 10
    }
)
print(f"Chat status: {chat_response.status_code}")
print(f"Chat response: {json.dumps(chat_response.json(), indent=2)}")