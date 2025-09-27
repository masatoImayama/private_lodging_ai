import uuid
from typing import List
from google.cloud import aiplatform
from app.schemas.dto import Chunk
from app.utils.pdf import extract_text_from_pdf
from app.utils.chunks import make_chunks


def embed_texts(texts: List[str], model_name: str = "text-embedding-005") -> List[List[float]]:
    """
    Generate embeddings for a list of texts using Vertex AI.

    Args:
        texts: List of text strings to embed
        model_name: Name of the embedding model

    Returns:
        List of embedding vectors
    """
    from vertexai.preview.language_models import TextEmbeddingInput, TextEmbeddingModel
    import vertexai
    from app.config import Config

    vertexai.init(project=Config.PROJECT_ID, location=Config.LOCATION)

    model = TextEmbeddingModel.from_pretrained(model_name)

    # Create TextEmbeddingInput objects with RETRIEVAL_DOCUMENT task type
    text_inputs = [
        TextEmbeddingInput(
            text=text,
            task_type="RETRIEVAL_DOCUMENT"  # Specify task type for document indexing
        )
        for text in texts
    ]

    embeddings = model.get_embeddings(text_inputs)

    return [embedding.values for embedding in embeddings]


def upsert_vectors(
    tenant_id: str,
    doc_id: str,
    chunks: List[Chunk],
    embeddings: List[List[float]],
    index_id: str,
    gcs_uri: str
) -> int:
    """
    Upsert vectors to Vertex AI Vector Search with namespace filtering.

    Args:
        tenant_id: Tenant identifier for namespace
        doc_id: Document identifier
        chunks: List of Chunk objects
        embeddings: List of embedding vectors
        index_id: Vector Search index ID
        gcs_uri: Original GCS URI of the document

    Returns:
        Number of vectors upserted
    """
    from app.config import Config
    import json
    from google.cloud import storage

    aiplatform.init(project=Config.PROJECT_ID, location=Config.LOCATION)

    try:

        # Save chunk texts to GCS (only this is needed, not full metadata)
        storage_client = storage.Client()
        bucket = storage_client.bucket(Config.BUCKET_NAME)

        # Store chunk texts in a simple format
        chunk_texts = {}
        for chunk in chunks:
            chunk_key = f"{tenant_id}_{doc_id}_{chunk.chunk_id}"
            chunk_texts[chunk_key] = {
                "text": chunk.text,
                "page": chunk.page,
                "checksum": chunk.checksum,
                "path": gcs_uri
            }

        # Save to GCS
        chunk_blob_name = f"chunks/{tenant_id}/{doc_id}.json"
        chunk_blob = bucket.blob(chunk_blob_name)
        chunk_blob.upload_from_string(
            json.dumps(chunk_texts),
            content_type="application/json"
        )

        # Use the basic aiplatform library for vector upsert
        aiplatform.init(project=Config.PROJECT_ID, location=Config.LOCATION)

        # Prepare datapoints for Vector Search
        datapoints = []
        for chunk, embedding in zip(chunks, embeddings):
            # Create IndexDatapoint with correct structure
            datapoint = {
                "datapoint_id": f"{tenant_id}_{doc_id}_{chunk.chunk_id}",
                "feature_vector": embedding
            }
            datapoints.append(datapoint)

        # Use the high-level aiplatform API for upsert operation
        from google.cloud import aiplatform

        # Initialize AI Platform
        aiplatform.init(project=Config.PROJECT_ID, location=Config.LOCATION)

        # Get the MatchingEngineIndex using high-level API
        index_name = f"projects/{Config.PROJECT_NUMBER}/locations/{Config.LOCATION}/indexes/{Config.INDEX_ID}"

        print(f"DEBUG - Using INDEX_ID: {Config.INDEX_ID}")
        print(f"DEBUG - Using DEPLOYED_INDEX_ID: {Config.DEPLOYED_INDEX_ID}")
        print(f"DEBUG - Constructed index_name: {index_name}")

        # Convert datapoints to proper format with namespace restrictions
        datapoints_for_upsert = []
        for chunk, embedding in zip(chunks, embeddings):
            datapoint = {
                "datapoint_id": f"{tenant_id}_{doc_id}_{chunk.chunk_id}",
                "feature_vector": embedding,
                "restricts": [
                    {
                        "namespace": "tenant_id",
                        "allow_list": [tenant_id]
                    }
                ]
            }
            datapoints_for_upsert.append(datapoint)

        # Use MatchingEngineIndex for upsert
        try:
            index = aiplatform.MatchingEngineIndex(index_name=index_name)

            # Perform the upsert operation using high-level API
            response = index.upsert_datapoints(
                datapoints=datapoints_for_upsert
            )
        except Exception as high_level_error:
            print(f"High-level API failed: {high_level_error}")
            print("Falling back to low-level API...")

            # Fallback to low-level API
            from google.cloud import aiplatform_v1

            client = aiplatform_v1.IndexServiceClient()

            # Convert to low-level format
            formatted_datapoints = []
            for dp in datapoints_for_upsert:
                formatted_datapoint = aiplatform_v1.IndexDatapoint(
                    datapoint_id=dp["datapoint_id"],
                    feature_vector=dp["feature_vector"],
                    restricts=[
                        aiplatform_v1.IndexDatapoint.Restriction(
                            namespace="tenant_id",
                            allow_list=[tenant_id]
                        )
                    ]
                )
                formatted_datapoints.append(formatted_datapoint)

            request = aiplatform_v1.UpsertDatapointsRequest(
                index=index_name,
                datapoints=formatted_datapoints
            )

            response = client.upsert_datapoints(request=request)

        print(f"Successfully upserted {len(chunks)} vectors to Vector Search")
        print(f"Chunk texts stored at: gs://{Config.BUCKET_NAME}/{chunk_blob_name}")
        print(f"Response: {response}")

        return len(chunks)

    except Exception as e:
        print(f"Error upserting vectors to Vector Search: {e}")
        import traceback
        traceback.print_exc()
        raise


async def process_document_ingestion(
    tenant_id: str,
    gcs_uri: str,
    doc_id: str,
    index_id: str
) -> dict:
    """
    Process document ingestion: extract, split, embed, and upsert.
    
    Args:
        tenant_id: Tenant identifier
        gcs_uri: GCS URI of the PDF file
        doc_id: Document identifier
        index_id: Vector Search index ID
        
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
        index_id=index_id,
        gcs_uri=gcs_uri
    )
    
    return {
        "job_id": job_id,
        "doc_id": doc_id,
        "chunks": num_chunks
    }