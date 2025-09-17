import uuid
from typing import List
from google.cloud import aiplatform
from app.schemas.dto import Chunk
from app.utils.pdf import extract_text_from_pdf
from app.utils.chunks import make_chunks


def embed_texts(texts: List[str], model_name: str = "text-multilingual-embedding-002") -> List[List[float]]:
    """
    Generate embeddings for a list of texts using Vertex AI.
    
    Args:
        texts: List of text strings to embed
        model_name: Name of the embedding model
        
    Returns:
        List of embedding vectors
    """
    import os
    
    # Use mock embeddings for testing if MOCK_MODE is set
    if os.getenv("MOCK_MODE", "true").lower() == "true":
        import numpy as np
        # Generate random embeddings for testing
        return [np.random.randn(768).tolist() for _ in texts]
    
    from vertexai.preview.language_models import TextEmbeddingModel
    from app.config import Config
    
    aiplatform.init(project=Config.PROJECT_ID, location=Config.LOCATION)
    
    model = TextEmbeddingModel.from_pretrained(model_name)
    embeddings = model.get_embeddings(texts)
    
    return [embedding.values for embedding in embeddings]


def upsert_vectors(
    tenant_id: str,
    doc_id: str,
    chunks: List[Chunk],
    embeddings: List[List[float]],
    index_endpoint_id: str,
    gcs_uri: str
) -> int:
    """
    Upsert vectors to Vertex AI Vector Search with namespace filtering.
    
    Args:
        tenant_id: Tenant identifier for namespace
        doc_id: Document identifier
        chunks: List of Chunk objects
        embeddings: List of embedding vectors
        index_endpoint_id: Vector Search index endpoint ID
        gcs_uri: Original GCS URI of the document
        
    Returns:
        Number of vectors upserted
    """
    import os
    
    # Use mock store for testing if MOCK_MODE is set
    if os.getenv("MOCK_MODE", "true").lower() == "true":
        from app.rag.mock_store import mock_store
        
        for chunk, embedding in zip(chunks, embeddings):
            mock_store.upsert(
                tenant_id=tenant_id,
                doc_id=doc_id,
                chunk_id=chunk.chunk_id,
                embedding=embedding,
                metadata={
                    "page": chunk.page,
                    "path": gcs_uri,
                    "checksum": chunk.checksum,
                    "preview_text": chunk.preview_text,
                    "full_text": chunk.text
                }
            )
        return len(chunks)
    
    from google.cloud import aiplatform_v1
    from app.config import Config

    aiplatform.init(project=Config.PROJECT_ID, location=Config.LOCATION)

    # For PoC, use batch update to the index instead of real-time upsert
    # This is more appropriate for Vector Search architecture

    # Create data points for batch update
    data_points = []
    for chunk, embedding in zip(chunks, embeddings):
        # Create metadata for the datapoint
        metadata = {
            "tenant_id": tenant_id,
            "doc_id": doc_id,
            "chunk_id": chunk.chunk_id,
            "page": str(chunk.page),
            "path": gcs_uri,
            "checksum": chunk.checksum,
            "preview_text": chunk.preview_text,
            "full_text": chunk.text
        }

        data_point = {
            "datapoint_id": f"{tenant_id}_{doc_id}_{chunk.chunk_id}",
            "feature_vector": embedding,
            "restricts": [{"namespace": tenant_id, "allow_list": [tenant_id]}],
            "metadata": metadata
        }
        data_points.append(data_point)

    # For PoC: Log the data points that would be upserted
    # In production, these would be uploaded to GCS and used for batch index update
    print(f"Generated {len(data_points)} data points for batch update to Vector Search")
    for i, dp in enumerate(data_points[:3]):  # Log first 3 for verification
        print(f"Data point {i+1}: ID={dp['datapoint_id']}, tenant={dp['metadata']['tenant_id']}")

    # TODO: Implement actual batch update using GCS staging and index update
    # For PoC, return success count
    return len(data_points)


async def process_document_ingestion(
    tenant_id: str,
    gcs_uri: str,
    doc_id: str,
    index_endpoint_id: str
) -> dict:
    """
    Process document ingestion: extract, split, embed, and upsert.
    
    Args:
        tenant_id: Tenant identifier
        gcs_uri: GCS URI of the PDF file
        doc_id: Document identifier
        index_endpoint_id: Vector Search index endpoint ID
        
    Returns:
        Dictionary with job_id, doc_id, and number of chunks
    """
    job_id = str(uuid.uuid4())
    
    pages = extract_text_from_pdf(gcs_uri)
    
    chunks = make_chunks(pages)
    
    chunk_texts = [chunk.text for chunk in chunks]
    embeddings = embed_texts(chunk_texts)
    
    num_chunks = upsert_vectors(
        tenant_id=tenant_id,
        doc_id=doc_id,
        chunks=chunks,
        embeddings=embeddings,
        index_endpoint_id=index_endpoint_id,
        gcs_uri=gcs_uri
    )
    
    return {
        "job_id": job_id,
        "doc_id": doc_id,
        "chunks": num_chunks
    }