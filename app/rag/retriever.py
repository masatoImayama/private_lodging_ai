from typing import List, Tuple
import numpy as np
from google.cloud import aiplatform
from app.schemas.dto import ChunkHit


def embed_query(query: str, model_name: str = "text-embedding-005") -> List[float]:
    """
    Generate embedding for a query using Vertex AI.

    Args:
        query: Query text to embed
        model_name: Name of the embedding model

    Returns:
        Embedding vector
    """
    from vertexai.preview.language_models import TextEmbeddingInput, TextEmbeddingModel
    import vertexai
    from app.config import Config

    vertexai.init(project=Config.PROJECT_ID, location=Config.LOCATION)

    model = TextEmbeddingModel.from_pretrained(model_name)

    text_input = TextEmbeddingInput(
        text=query,
        task_type="RETRIEVAL_QUERY"  # Specify task type for search queries
    )

    embeddings = model.get_embeddings([text_input])

    return embeddings[0].values


def vector_search(
    tenant_id: str,
    query_embedding: List[float],
    index_endpoint_id: str,
    top_k: int = 30
) -> List[Tuple[str, float, dict]]:
    """
    Perform vector search with namespace filtering using Vertex AI Vector Search.

    Args:
        tenant_id: Tenant identifier for namespace filtering
        query_embedding: Query embedding vector
        index_endpoint_id: Vector Search index endpoint ID
        top_k: Number of results to retrieve

    Returns:
        List of tuples (datapoint_id, distance, metadata)
    """
    from app.config import Config
    import json
    from google.cloud import storage

    try:
        # Use the basic aiplatform library for vector search
        from google.cloud import aiplatform

        aiplatform.init(project=Config.PROJECT_ID, location=Config.LOCATION)

        # 🔧 修正: PROJECT_NUMBER を使用してエンドポイントを指定
        index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=f"projects/{Config.PROJECT_NUMBER}/locations/{Config.LOCATION}/indexEndpoints/{Config.INDEX_ENDPOINT_ID}"
        )

        # Perform vector search
        # Note: High-level API doesn't support namespace filtering directly
        # We'll filter results manually based on datapoint_id prefix
        print(f"DEBUG: Query executed for tenant: {tenant_id}")

        response = index_endpoint.find_neighbors(
            deployed_index_id=Config.DEPLOYED_INDEX_ID,
            queries=[query_embedding],
            num_neighbors=top_k
        )

        print(f"DEBUG: Response type: {type(response)}")
        print(f"DEBUG: Response length: {len(response) if response else 0}")

        # Process results - find_neighbors returns a list of Neighbor objects directly
        results = []
        if response and len(response) > 0:
            print(f"DEBUG: Response is a list of {len(response)} neighbors")
            print(f"DEBUG: First neighbor type: {type(response[0])}")

            # 最初の5件のIDを詳細表示
            for i, neighbor in enumerate(response[:5]):
                print(f"DEBUG: Neighbor {i}: ID='{neighbor.id}', Distance={neighbor.distance}, Type={type(neighbor.id)}")

            # Process each neighbor directly from response
            for neighbor in response:
                datapoint_id = neighbor.id
                # Parse datapoint_id to extract metadata
                # Format: {tenant_id}_{doc_id}_{chunk_id}
                parts = datapoint_id.split('_', 2)

                print(f"DEBUG: Processing {datapoint_id}, parts={parts}, expected tenant={tenant_id}")

                # 🔧 Manual tenant filtering: skip if tenant_id doesn't match
                if len(parts) > 0 and parts[0] != tenant_id:
                    print(f"DEBUG: Skipped due to tenant mismatch: {parts[0]} != {tenant_id}")
                    continue

                metadata = {
                    "tenant_id": parts[0] if len(parts) > 0 else "",
                    "doc_id": parts[1] if len(parts) > 1 else "",
                    "chunk_id": parts[2] if len(parts) > 2 else "",
                    "datapoint_id": datapoint_id
                }

                results.append((
                    datapoint_id,
                    neighbor.distance,
                    metadata
                ))
        else:
            print(f"DEBUG: Empty or no response from vector search. Response: {response}")

        print(f"Vector search returned {len(results)} results for tenant {tenant_id}")

        # Load chunk texts from GCS to get full text
        storage_client = storage.Client()
        bucket = storage_client.bucket(Config.BUCKET_NAME)

        # Group results by doc_id to minimize GCS reads
        doc_chunks = {}
        for datapoint_id, distance, metadata in results:
            doc_id = metadata.get("doc_id", "")
            if doc_id not in doc_chunks:
                doc_chunks[doc_id] = []
            doc_chunks[doc_id].append((datapoint_id, distance, metadata))

        # Load chunk texts and enhance results
        enhanced_results = []
        for doc_id, doc_results in doc_chunks.items():
            chunk_texts = {}
            try:
                # Load chunk texts for this document
                chunk_blob_name = f"chunks/{tenant_id}/{doc_id}.json"
                chunk_blob = bucket.blob(chunk_blob_name)
                if chunk_blob.exists():
                    chunk_data = json.loads(chunk_blob.download_as_text())
                    chunk_texts = chunk_data
                    print(f"Loaded {len(chunk_texts)} chunks for doc {doc_id}")
                else:
                    print(f"Warning: Chunk file not found: {chunk_blob_name}")
            except Exception as e:
                print(f"Warning: Could not load chunk texts for {doc_id}: {e}")

            # Enhance metadata for each result
            for datapoint_id, distance, metadata in doc_results:
                chunk_info = chunk_texts.get(datapoint_id, {})
                enhanced_metadata = metadata.copy()
                enhanced_metadata["full_text"] = chunk_info.get("text", "")
                enhanced_metadata["preview_text"] = chunk_info.get("text", "")[:200]
                enhanced_metadata["path"] = chunk_info.get("path", "")
                enhanced_metadata["checksum"] = chunk_info.get("checksum", "")
                enhanced_metadata["page"] = chunk_info.get("page", metadata.get("page", 1))

                enhanced_results.append((datapoint_id, distance, enhanced_metadata))

        print(f"Enhanced results: {len(enhanced_results)} chunks with text loaded")
        return enhanced_results

    except Exception as e:
        print(f"Error in vector search: {e}")
        import traceback
        traceback.print_exc()
        return []


def apply_mmr(
    hits: List[ChunkHit],
    query_embedding: List[float],
    lambda_param: float = 0.5,
    top_k: int = 15
) -> List[ChunkHit]:
    """
    Apply Maximum Marginal Relevance (MMR) to diversify results.
    
    Args:
        hits: List of ChunkHit objects
        query_embedding: Query embedding vector
        lambda_param: Balance between relevance and diversity (0-1)
        top_k: Number of results to return
        
    Returns:
        List of diversified ChunkHit objects
    """
    if len(hits) <= top_k:
        return hits
    
    selected = []
    candidates = hits.copy()
    
    first_idx = 0
    selected.append(candidates.pop(first_idx))
    
    while len(selected) < top_k and candidates:
        mmr_scores = []
        
        for candidate in candidates:
            relevance_score = candidate.score
            
            max_similarity = 0
            for selected_hit in selected:
                similarity = calculate_text_similarity(
                    candidate.preview_text,
                    selected_hit.preview_text
                )
                max_similarity = max(max_similarity, similarity)
            
            mmr_score = lambda_param * relevance_score - (1 - lambda_param) * max_similarity
            mmr_scores.append(mmr_score)
        
        best_idx = np.argmax(mmr_scores)
        selected.append(candidates.pop(best_idx))
    
    return selected


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple text similarity based on common tokens.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score (0-1)
    """
    tokens1 = set(text1.lower().split())
    tokens2 = set(text2.lower().split())
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    
    return intersection / union if union > 0 else 0.0


async def search(
    tenant_id: str,
    query: str,
    index_endpoint_id: str,
    top_k_vector: int = 30,
    top_k_final: int = 15
) -> List[ChunkHit]:
    """
    Search for relevant chunks with namespace filtering and MMR.
    
    Args:
        tenant_id: Tenant identifier
        query: User query
        index_endpoint_id: Vector Search index endpoint ID
        top_k_vector: Number of results to retrieve from vector search
        top_k_final: Number of results to return after MMR
        
    Returns:
        List of ChunkHit objects
    """
    query_embedding = embed_query(query)

    search_results = vector_search(
        tenant_id=tenant_id,
        query_embedding=query_embedding,
        index_endpoint_id=index_endpoint_id,
        top_k=top_k_vector
    )

    hits = []
    for datapoint_id, distance, metadata in search_results:
        score = 1.0 / (1.0 + distance)

        hit = ChunkHit(
            chunk_id=metadata.get("chunk_id", ""),
            doc_id=metadata.get("doc_id", ""),
            page=int(metadata.get("page", 1)),
            path=metadata.get("path", ""),
            checksum=metadata.get("checksum", ""),
            preview_text=metadata.get("preview_text", ""),
            score=score,
            full_text=metadata.get("full_text", "")
        )
        hits.append(hit)
    
    print(f"Created {len(hits)} ChunkHit objects")
    
    diversified_hits = apply_mmr(
        hits=hits,
        query_embedding=query_embedding,
        lambda_param=0.6,
        top_k=top_k_final
    )
    
    print(f"After MMR: {len(diversified_hits)} diversified hits")
    return diversified_hits