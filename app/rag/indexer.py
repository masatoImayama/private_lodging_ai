import uuid
from typing import List
from google.cloud import aiplatform
from app.schemas.dto import Chunk
from app.utils.pdf import extract_text_from_pdf
from app.utils.chunks import make_chunks


def embed_texts(texts: List[str], model_name: str = "text-embedding-004") -> List[List[float]]:
    """
    Generate embeddings for a list of texts using Vertex AI.
    
    Args:
        texts: List of text strings to embed
        model_name: Name of the embedding model
        
    Returns:
        List of embedding vectors
    """
    from vertexai.language_models import TextEmbeddingModel
    
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
    from google.cloud import aiplatform_v1
    
    index_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_id)
    
    data_points = []
    for chunk, embedding in zip(chunks, embeddings):
        data_point = aiplatform_v1.IndexDatapoint(
            datapoint_id=f"{tenant_id}_{doc_id}_{chunk.chunk_id}",
            feature_vector=embedding,
            restricts=[
                aiplatform_v1.IndexDatapoint.Restriction(
                    namespace=tenant_id,
                    allow_list=[tenant_id]
                )
            ]
        )
        
        data_point.metadata = {
            "tenant_id": tenant_id,
            "doc_id": doc_id,
            "chunk_id": chunk.chunk_id,
            "page": str(chunk.page),
            "path": gcs_uri,
            "checksum": chunk.checksum,
            "preview_text": chunk.preview_text,
            "full_text": chunk.text
        }
        
        data_points.append(data_point)
    
    index_endpoint.upsert_datapoints(data_points)
    
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