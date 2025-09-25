"""Firestore-based vector search implementation (low-cost alternative to Vertex AI Vector Search)"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.vector_query import VectorQuery
import google.generativeai as genai
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class FirestoreRetriever:
    """Low-cost vector search using Firestore's native vector search capability"""

    def __init__(self):
        self.db = firestore.Client(project=os.getenv('PROJECT_ID', 'private-lodging-ai'))
        self.collection_name = 'vectors'

        # Initialize embedding model
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.embed_model = genai.GenerativeModel('models/text-embedding-004')

    def upsert_vectors(
        self,
        tenant_id: str,
        doc_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> int:
        """Insert or update vectors in Firestore"""
        try:
            batch = self.db.batch()
            count = 0

            for chunk, embedding in zip(chunks, embeddings):
                # Create unique document ID
                vector_id = f"{tenant_id}_{doc_id}_{chunk['chunk_id']}"
                doc_ref = self.db.collection(self.collection_name).document(vector_id)

                # Prepare document data
                data = {
                    'tenant_id': tenant_id,
                    'doc_id': doc_id,
                    'chunk_id': chunk['chunk_id'],
                    'page': chunk.get('page', 0),
                    'text': chunk['text'][:2000],  # Store first 2000 chars
                    'checksum': chunk.get('checksum', ''),
                    'path': chunk.get('path', ''),
                    'embedding': Vector(embedding),  # Firestore Vector type
                    'timestamp': datetime.utcnow(),
                    'metadata': chunk.get('metadata', {})
                }

                batch.set(doc_ref, data)
                count += 1

                # Commit batch every 500 documents
                if count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()

            # Commit remaining documents
            if count % 500 != 0:
                batch.commit()

            logger.info(f"Upserted {count} vectors for tenant {tenant_id}, doc {doc_id}")
            return count

        except Exception as e:
            logger.error(f"Error upserting vectors: {str(e)}")
            raise

    def search(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 15,
        filter_doc_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search vectors using Firestore vector search"""
        try:
            # Generate query embedding
            result = self.embed_model.generate_embeddings(
                content=query,
                task_type="retrieval_document",
                title="Query"
            )
            query_embedding = result['embedding']

            # Build Firestore query
            collection = self.db.collection(self.collection_name)

            # Apply tenant filter
            query_ref = collection.where('tenant_id', '==', tenant_id)

            # Apply document filter if specified
            if filter_doc_ids:
                query_ref = query_ref.where('doc_id', 'in', filter_doc_ids)

            # Execute vector search
            vector_query = query_ref.find_nearest(
                vector_field='embedding',
                query_vector=Vector(query_embedding),
                distance_measure='DOT_PRODUCT',
                limit=top_k
            )

            # Process results
            results = []
            for doc in vector_query.stream():
                data = doc.to_dict()
                results.append({
                    'doc_id': data['doc_id'],
                    'chunk_id': data['chunk_id'],
                    'page': data['page'],
                    'text': data['text'],
                    'checksum': data['checksum'],
                    'path': data['path'],
                    'score': data.get('_distance', 0),  # Similarity score
                    'metadata': data.get('metadata', {})
                })

            # Sort by score (higher is better for DOT_PRODUCT)
            results.sort(key=lambda x: x['score'], reverse=True)

            logger.info(f"Found {len(results)} results for tenant {tenant_id}")
            return results[:top_k]

        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            raise

    def delete_by_doc(self, tenant_id: str, doc_id: str) -> int:
        """Delete all vectors for a specific document"""
        try:
            # Query documents to delete
            query = (self.db.collection(self.collection_name)
                    .where('tenant_id', '==', tenant_id)
                    .where('doc_id', '==', doc_id))

            # Delete in batches
            batch = self.db.batch()
            count = 0

            for doc in query.stream():
                batch.delete(doc.reference)
                count += 1

                if count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()

            if count % 500 != 0:
                batch.commit()

            logger.info(f"Deleted {count} vectors for doc {doc_id}")
            return count

        except Exception as e:
            logger.error(f"Error deleting vectors: {str(e)}")
            raise

    def create_index(self):
        """Create Firestore index for vector search (run once)"""
        # This needs to be done via gcloud CLI or Firebase console
        print("""
        To enable vector search, create an index with:

        gcloud firestore indexes composite create \\
          --collection-group=vectors \\
          --field-config field-path=tenant_id,order=ASCENDING \\
          --field-config field-path=embedding,vector-config='{"dimension": 768, "flat": {}}' \\
          --project={PROJECT_ID}
        """)