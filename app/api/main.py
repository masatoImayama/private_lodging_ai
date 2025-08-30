import time
from typing import List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.config import Config
from app.schemas.dto import (
    IngestRequest, IngestResponse,
    ChatRequest, ChatResponse,
    Citation
)
from app.rag.indexer import process_document_ingestion
from app.rag.retriever import search
from app.rag.generator import generate_answer_with_retry


app = FastAPI(
    title="Private Lodging RAG API",
    description="Retrieval-Augmented Generation API for private lodging documents",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize configuration and services on startup."""
    try:
        Config.initialize_aiplatform()
    except Exception as e:
        raise RuntimeError(f"Failed to initialize services: {str(e)}")


@app.get("/healthz", status_code=200)
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest):
    """
    Ingest a PDF document from GCS.
    
    Process flow:
    1. Extract text from PDF
    2. Split into chunks
    3. Generate embeddings
    4. Upsert to Vector Search with namespace filtering
    """
    if not request.tenant_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id cannot be empty"
        )
    
    try:
        result = await process_document_ingestion(
            tenant_id=request.tenant_id,
            gcs_uri=request.gcs_uri,
            doc_id=request.doc_id,
            index_endpoint_id=Config.INDEX_ENDPOINT_ID
        )
        
        if result["chunks"] == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No chunks were created from the document"
            )
        
        return IngestResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document ingestion failed: {str(e)}"
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with documents using RAG.
    
    Process flow:
    1. Vector search with namespace filtering
    2. Apply MMR for result diversification
    3. Generate answer with mandatory citations
    """
    if not request.tenant_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id cannot be empty"
        )
    
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="query cannot be empty"
        )
    
    start_time = time.perf_counter()
    
    try:
        hits = await search(
            tenant_id=request.tenant_id,
            query=request.query,
            index_endpoint_id=Config.INDEX_ENDPOINT_ID,
            top_k_vector=30,
            top_k_final=request.top_k
        )
        
        if not hits:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No relevant documents found for the query"
            )
        
        answer, citations = await generate_answer_with_retry(
            query=request.query,
            hits=hits,
            max_retries=2
        )
        
        if not citations:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No citations could be generated for the answer"
            )
        
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        
        return ChatResponse(
            answer=answer,
            citations=citations,
            latency_ms=latency_ms
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        if "citations" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat request failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)