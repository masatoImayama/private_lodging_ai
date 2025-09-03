"""
Mock in-memory vector store for testing RAG functionality without Vertex AI Vector Search.
"""
import hashlib
import numpy as np
from typing import List, Dict, Any, Tuple
from app.schemas.dto import ChunkHit


class MockVectorStore:
    """In-memory vector store for testing."""
    
    def __init__(self):
        self.vectors: Dict[str, Dict[str, Any]] = {}
        self.dimension = 768
    
    def upsert(
        self,
        tenant_id: str,
        doc_id: str,
        chunk_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        """Store vector with metadata."""
        vector_id = f"{tenant_id}_{doc_id}_{chunk_id}"
        self.vectors[vector_id] = {
            "tenant_id": tenant_id,
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "embedding": np.array(embedding),
            "metadata": metadata
        }
    
    def search(
        self,
        tenant_id: str,
        query_embedding: List[float],
        top_k: int = 10
    ) -> List[ChunkHit]:
        """Search for similar vectors within a tenant namespace."""
        query_vec = np.array(query_embedding)
        
        results = []
        for vector_id, data in self.vectors.items():
            if data["tenant_id"] != tenant_id:
                continue
            
            # Compute cosine similarity
            similarity = np.dot(query_vec, data["embedding"]) / (
                np.linalg.norm(query_vec) * np.linalg.norm(data["embedding"])
            )
            # Ensure score is non-negative (convert from [-1, 1] to [0, 1])
            similarity = (similarity + 1.0) / 2.0
            
            results.append((similarity, data))
        
        # Sort by similarity descending
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Convert to ChunkHit objects
        hits = []
        for score, data in results[:top_k]:
            hits.append(ChunkHit(
                doc_id=data["doc_id"],
                chunk_id=data["chunk_id"],
                page=data["metadata"]["page"],
                path=data["metadata"]["path"],
                checksum=data["metadata"]["checksum"],
                preview_text=data["metadata"]["preview_text"],
                full_text=data["metadata"]["full_text"],
                score=float(score)
            ))
        
        return hits
    
    def clear(self):
        """Clear all vectors."""
        self.vectors.clear()


# Global mock store instance
mock_store = MockVectorStore()