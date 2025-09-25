import asyncio
import sys
sys.path.append('.')

from app.rag.retriever import embed_query
from app.rag.indexer import embed_texts

async def test_migration():
    """移行後の動作確認テスト"""

    # 1. 単一クエリのエンベディング
    print("Testing single query embedding...")
    try:
        query = "Gemini 1.5 Flash のテスト"
        embedding = embed_query(query)
        print(f"✅ Query embedding dimension: {len(embedding)}")
    except Exception as e:
        print(f"❌ Query embedding failed: {e}")

    # 2. バッチエンベディング
    print("\nTesting batch embedding...")
    try:
        texts = [
            "これはテスト文書1です",
            "これはテスト文書2です",
            "これはテスト文書3です"
        ]
        embeddings = embed_texts(texts)
        print(f"✅ Batch embedding count: {len(embeddings)}")
        print(f"✅ First embedding dimension: {len(embeddings[0])}")
    except Exception as e:
        print(f"❌ Batch embedding failed: {e}")

    print("\n移行テスト完了")

if __name__ == "__main__":
    asyncio.run(test_migration())