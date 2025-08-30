from typing import List, Tuple
import numpy as np
from google.cloud import aiplatform
from app.schemas.dto import ChunkHit


def embed_query(query: str, model_name: str = "text-embedding-004") -> List[float]:
    """
    Generate embedding for a query using Vertex AI.
    
    Args:
        query: Query text to embed
        model_name: Name of the embedding model
        
    Returns:
        Embedding vector
    """
    from vertexai.language_models import TextEmbeddingModel
    
    model = TextEmbeddingModel.from_pretrained(model_name)
    embeddings = model.get_embeddings([query])
    
    return embeddings[0].values


def vector_search(
    tenant_id: str,
    query_embedding: List[float],
    index_endpoint_id: str,
    top_k: int = 30
) -> List[Tuple[str, float, dict]]:
    """
    Perform vector search with namespace filtering.
    
    Args:
        tenant_id: Tenant identifier for namespace filtering
        query_embedding: Query embedding vector
        index_endpoint_id: Vector Search index endpoint ID
        top_k: Number of results to retrieve
        
    Returns:
        List of tuples (datapoint_id, distance, metadata)
    """
    from google.cloud import aiplatform_v1
    
    index_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_id)
    
    response = index_endpoint.find_neighbors(
        deployed_index_id=index_endpoint.deployed_indexes[0].id,
        queries=[query_embedding],
        num_neighbors=top_k,
        filter=aiplatform_v1.IndexDatapoint.Restriction(
            namespace=tenant_id,
            allow_list=[tenant_id]
        )
    )
    
    results = []
    for neighbor_list in response:
        for neighbor in neighbor_list.neighbors:
            results.append((
                neighbor.datapoint_id,
                neighbor.distance,
                neighbor.datapoint.metadata
            ))
    
    return results


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
    
    diversified_hits = apply_mmr(
        hits=hits,
        query_embedding=query_embedding,
        lambda_param=0.6,
        top_k=top_k_final
    )
    
    return diversified_hits