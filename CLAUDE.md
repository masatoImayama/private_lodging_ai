# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Overview

RAG (Retrieval-Augmented Generation) API using GCP Vertex AI + Vector Search. Provides PDF document ingestion and tenant-isolated chat functionality.

**Endpoints:**
- `POST /ingest`: PDF ingestion (extract → chunk → embed → index)
- `POST /chat`: RAG-based Q&A with mandatory citations
- `GET /healthz`: Health check

## Architecture

```
/app
  /api
    main.py            # FastAPI app: /ingest /chat /healthz
  /rag
    indexer.py         # Document processing: extract→split→embed→upsert
    retriever.py       # Vector search with namespace filtering + MMR
    generator.py       # Gemini answer generation with citations
  /schemas
    dto.py             # Pydantic models (request/response)
  /utils
    pdf.py             # pypdf text extraction
    chunks.py          # Text chunking (size=1400, overlap=160)
    hash.py            # sha256 checksum
  config.py           # Environment config with validation
```

**Key Components:**
- **Tenant Isolation**: All vector search operations use `namespace=tenant_id` for data separation
- **Citations Required**: All answers must include citations (doc_id, page, path, chunk_id, checksum)
- **Storage Strategy**:
  - Raw PDFs stored in GCS
  - Chunk metadata stored in GCS at `chunks/{tenant_id}/{doc_id}.json`
  - Vectors stored in Vertex AI Vector Search
- **Embedding Model**: text-embedding-005 (768 dimensions, task_type=RETRIEVAL_DOCUMENT for indexing, RETRIEVAL_QUERY for search)
- **Generation Model**: gemini-2.5-flash (temperature=0.0, max_tokens=1500)
  - **IMPORTANT**: Gemini 1.5 series was retired April 2025. Use gemini-2.5-flash or gemini-2.5-pro only
- **Retrieval Strategy**: Top 30 from vector search → MMR (lambda=0.6) → Top 15 final results

## Environment Configuration

Required environment variables:
```
PROJECT_ID           # GCP project ID (use PROJECT_ID, not PROJECT_NUMBER for index operations)
PROJECT_NUMBER       # GCP project number (863645902320)
LOCATION             # GCP region (us-central1 for production)
BUCKET_NAME          # GCS bucket name
INDEX_ID             # Vector Search index ID (6734414162128011264)
INDEX_ENDPOINT_ID    # Vector Search endpoint ID (7867526865248845824)
DEPLOYED_INDEX_ID    # Deployed index ID (private_lodging_stream_v1)
```

**Important**: Index resource names use `projects/{PROJECT_ID}/locations/{LOCATION}/indexes/{INDEX_ID}` format.

## Common Commands

### Local Development

```bash
# Setup virtual environment
python -m venv venv
./venv/Scripts/activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run server locally
uvicorn app.api.main:app --reload --port 8080

# Access Swagger UI
http://localhost:8080/docs
```

### Build & Deploy

```bash
# Get current commit SHA
git rev-parse --short HEAD

# Build and deploy with Cloud Build (requires SHORT_SHA substitution)
gcloud builds submit --config cloudbuild.yaml --substitutions=SHORT_SHA=$(git rev-parse --short HEAD) .

# Check deployment status
gcloud run services describe private-lodging-ai --region us-central1

# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=private-lodging-ai" --limit 50
```

### Testing

```bash
# Health check
curl http://localhost:8080/healthz

# Ingest document
curl -X POST "http://localhost:8080/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "t_001",
    "gcs_uri": "gs://bucket-name/file.pdf",
    "doc_id": "doc-2025-001"
  }'

# Chat query
curl -X POST "http://localhost:8080/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "t_001",
    "query": "質問内容",
    "top_k": 15
  }'
```

### GCP Operations

```bash
# Check Vector Search index status
gcloud ai indexes describe {INDEX_ID} --region={LOCATION}

# List index endpoints
gcloud ai index-endpoints list --region={LOCATION}

# Check deployed indexes
gcloud ai index-endpoints describe {INDEX_ENDPOINT_ID} --region={LOCATION}
```

## Implementation Constraints

- **Runtime**: Python 3.11 / FastAPI on Cloud Run
- **Embedding**: text-embedding-005 (768 dimensions)
- **Generation**: gemini-2.5-flash (NOT gemini-1.5-* - those models were retired)
- **Vector Search**: Vertex AI Vector Search (existing index/endpoint)
- **Storage**: GCS for PDFs and chunk metadata
- **Chunking**: chunk_size=1400, overlap=160
- **Encoding**: UTF-8
- **Processing**: Synchronous for PoC (design functions for future async conversion)

## Acceptance Criteria

- `POST /ingest` registers N chunks to index (minimum 1)
- `POST /chat` returns within 10 seconds with:
  - Natural language answer
  - Citation array (doc_id, page, path, chunk_id, checksum)
  - Latency in milliseconds
- Vector operations use namespace=tenant_id (no cross-tenant data leakage)
- Answer generation enforces mandatory citations (retry or error on zero citations)
- Works in both local (uvicorn) and Cloud Run deployment

## Important Coding Rules

**Do NOT implement mock functionality** unless explicitly instructed. Mock implementations provide no value. Always work towards correct real implementation.

## Data Flow

**Ingestion Flow:**
1. Download PDF from GCS to temp location
2. Extract text with pypdf (page by page)
3. Split into chunks (1400 chars, 160 overlap)
4. Generate embeddings (text-embedding-005, RETRIEVAL_DOCUMENT)
5. Store chunk metadata in GCS (`chunks/{tenant_id}/{doc_id}.json`)
6. Upsert vectors to Vector Search with datapoint_id format: `{tenant_id}_{doc_id}_{chunk_id}`

**Chat Flow:**
1. Generate query embedding (text-embedding-005, RETRIEVAL_QUERY)
2. Vector search (top 30, namespace=tenant_id)
3. Parse datapoint_id to extract tenant_id, doc_id, chunk_id
   - Format: `{tenant_id}_{doc_id}_{chunk_id}` (e.g., `t_003_doc-2025-003_c-00004`)
   - Split on underscore: tenant_id = first 2 parts (`t_003`), doc_id = 3rd part, chunk_id = remaining parts
   - Filter results by tenant_id match for isolation
4. Load chunk texts from GCS at `chunks/{tenant_id}/{doc_id}.json`
5. Apply MMR for diversity (compress to 10-15 results)
6. Generate answer with Gemini using full chunk texts
7. Extract and return citations from response (fallback to all hits if model returns empty citations)

## Error Handling

- Invalid GCS path → 404 Bad Request
- PDF extraction failure → 500 Internal Server Error
- Empty tenant_id → 400 Bad Request
- Zero citations → 409 Conflict or 422 Unprocessable Entity
- Embedding/generation API failures → 500 Internal Server Error with retry logic (using tenacity)

## Critical Troubleshooting

**Gemini Model Not Found (404 Publisher Model not found)**
- **Cause**: Using retired Gemini 1.5 model names (gemini-1.5-flash, gemini-1.5-pro, gemini-1.0-pro)
- **Solution**: Update to gemini-2.5-flash or gemini-2.5-pro in generator.py
- **Import Path**: Use `from vertexai.preview.generative_models import GenerativeModel`

**Vector Search Returns No Results**
- Check DEPLOYED_INDEX_ID matches actual deployment: `gcloud ai index-endpoints describe {INDEX_ENDPOINT_ID} --region={LOCATION}`
- Verify INDEX_ID is correct: `gcloud ai indexes describe {INDEX_ID} --region={LOCATION}`
- Ensure datapoint_id format matches: `{tenant_id}_{doc_id}_{chunk_id}`

**Tenant Isolation Failing**
- Verify datapoint_id parsing in retriever.py correctly splits tenant_id (first 2 underscore-separated parts)
- Check GCS chunk metadata path: `chunks/{tenant_id}/{doc_id}.json`
- Confirm tenant filtering logic excludes non-matching tenant_ids

**Empty/Missing Chunk Text**
- Verify chunk metadata file exists in GCS: `gsutil ls gs://{BUCKET}/chunks/{tenant_id}/`
- Check doc_id parsing doesn't incorrectly merge with chunk_id
- Ensure datapoint_id in chunk metadata JSON matches vector search results