from typing import List, Optional
from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1, description="Tenant identifier")
    gcs_uri: str = Field(..., pattern=r"^gs://.*", description="GCS URI of the PDF file")
    doc_id: str = Field(..., min_length=1, description="Document identifier")


class IngestResponse(BaseModel):
    job_id: str = Field(..., description="Job identifier")
    doc_id: str = Field(..., description="Document identifier")
    chunks: int = Field(..., ge=0, description="Number of chunks created")


class ChatRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1, description="Tenant identifier")
    query: str = Field(..., min_length=1, description="User query")
    top_k: int = Field(15, ge=1, le=50, description="Number of top results to retrieve")


class Citation(BaseModel):
    doc_id: str = Field(..., description="Document identifier")
    page: int = Field(..., ge=1, description="Page number")
    path: str = Field(..., description="GCS path to the original document")
    chunk_id: str = Field(..., description="Chunk identifier")
    checksum: str = Field(..., description="SHA256 checksum of the chunk")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Generated answer")
    citations: List[Citation] = Field(..., description="List of citations")
    latency_ms: int = Field(..., ge=0, description="Response latency in milliseconds")


class PageText(BaseModel):
    page_num: int = Field(..., ge=1, description="Page number")
    text: str = Field(..., description="Page text content")


class Chunk(BaseModel):
    chunk_id: str = Field(..., description="Chunk identifier")
    text: str = Field(..., description="Chunk text content")
    page: int = Field(..., ge=1, description="Page number")
    checksum: str = Field(..., description="SHA256 checksum")
    preview_text: str = Field(..., description="Preview text (first 200 chars)")


class ChunkHit(BaseModel):
    chunk_id: str = Field(..., description="Chunk identifier")
    doc_id: str = Field(..., description="Document identifier")
    page: int = Field(..., ge=1, description="Page number")
    path: str = Field(..., description="GCS path")
    checksum: str = Field(..., description="SHA256 checksum")
    preview_text: str = Field(..., description="Preview text")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    full_text: Optional[str] = Field(None, description="Full chunk text (optional)")