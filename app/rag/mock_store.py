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


# Global mock store instance with persistence simulation
mock_store = MockVectorStore()

# For demo purposes, pre-populate with sample data
def initialize_demo_data():
    """Initialize mock store with sample data for demo."""
    if not mock_store.vectors:  # Only initialize if empty
        sample_embedding = [0.1] * 768  # Simple embedding
        mock_store.upsert(
            tenant_id="t_003",
            doc_id="doc-2025-003",
            chunk_id="c-00001",
            embedding=sample_embedding,
            metadata={
                "page": 1,
                "path": "gs://private-lodging-ai-prod-data/sample.txt",
                "checksum": "sha256:sample123",
                "preview_text": "基本情報 物件名：YOOSUU上野/YOOSUU UENO",
                "full_text": "基本情報\n物件名：YOOSUU上野/YOOSUU UENO\n物件説明：当物件は東京都のJR御徒町駅に位置します。繁華街の中の住宅街で、静かでプライバシーが保たれています。羽田・成田空港へ直通、上野・秋葉原などの有名観光地へも1駅でアクセス可能で交通至便です。"
            }
        )
        mock_store.upsert(
            tenant_id="t_003",
            doc_id="doc-2025-003",
            chunk_id="c-00002",
            embedding=[0.2] * 768,
            metadata={
                "page": 1,
                "path": "gs://private-lodging-ai-prod-data/sample.txt",
                "checksum": "sha256:sample456",
                "preview_text": "所在地 郵便番号：110-0016",
                "full_text": "所在地\n郵便番号：110-0016\n日本語住所：東京都台東区台東３丁目１１ー１０　ルネサンスコート御徒町\n英語住所：Renaissance Court Okachimachi, 3 Chome-11-10 Taito, Taito City, Tokyo"
            }
        )
        mock_store.upsert(
            tenant_id="t_003",
            doc_id="doc-2025-003",
            chunk_id="c-00003",
            embedding=[0.3] * 768,
            metadata={
                "page": 1,
                "path": "gs://private-lodging-ai-prod-data/sample.txt",
                "checksum": "sha256:sample789",
                "preview_text": "オーナーおすすめ 食事：モンゴルタンメン中本",
                "full_text": "オーナーおすすめ\n食事：モンゴルタンメン中本 御徒町店（ランチ・ディナーに最適）住所:〒110-0005 東京都台東区上野 ラーメン横丁内、アパートから450m、徒歩7分。初めての方は看板メニューの北極ラーメンがおすすめ。"
            }
        )

# Initialize demo data when module is imported
initialize_demo_data()