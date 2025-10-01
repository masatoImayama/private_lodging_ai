import json
from typing import List, Tuple
from google.cloud import aiplatform
from app.schemas.dto import ChunkHit, Citation


def generate_answer(
    query: str,
    hits: List[ChunkHit],
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.0,  # より決定論的に
    max_tokens: int = 1500  # トークン数を増やす
) -> Tuple[str, List[Citation]]:
    """
    Generate answer using Gemini with mandatory citations.
    """
    # ===== 詳細デバッグ情報 =====
    print("\n" + "="*80)
    print(f"QUERY: {query}")
    print(f"NUMBER OF HITS: {len(hits)}")

    if not hits:
        raise ValueError("No context chunks provided for answer generation")

    for i, hit in enumerate(hits, 1):
        print(f"\n--- Hit {i} ---")
        print(f"doc_id: {hit.doc_id}")
        print(f"page: {hit.page}")
        print(f"chunk_id: {hit.chunk_id}")
        print(f"score: {getattr(hit, 'score', 'N/A')}")
        print(f"full_text length: {len(hit.full_text) if hit.full_text else 0}")
        print(f"preview_text length: {len(hit.preview_text) if hit.preview_text else 0}")

        # 実際のテキスト内容を表示
        text = hit.full_text if hit.full_text else hit.preview_text
        print(f"Text content: {text[:200] if text else '[EMPTY]'}")

    print("="*80 + "\n")
    # ===== ここまで =====

    context = format_context_for_prompt(hits)

    print(f"Context length: {len(context)} characters")
    print(f"Context preview:\n{context[:800]}\n{'='*50}")

    system_prompt = """あなたは社内ドキュメントに基づいて正確に回答するアシスタントです。

【重要な指示】
- 以下の「参考資料」に記載されている情報のみを使って回答してください
- 参考資料に答えがある場合は、必ずその情報を使って回答してください
- 回答に使用したチャンクの情報を必ずcited_chunksに含めてください
- cited_chunksを空にすることは絶対に禁止です

【出力形式】※必ずこのJSON形式で出力してください
{
  "answer": "参考資料に基づいた具体的な回答",
  "cited_chunks": [
    {
      "doc_id": "参考資料に記載のdoc_id",
      "page": 参考資料に記載のpage番号,
      "path": "参考資料に記載のpath",
      "chunk_id": "参考資料に記載のchunk_id",
      "checksum": "参考資料に記載のchecksum"
    }
  ]
}

【例】
もし参考資料に「施設名はホテルサンシャインです」と書かれていたら:
{
  "answer": "施設の名前は「ホテルサンシャイン」です。",
  "cited_chunks": [
    {
      "doc_id": "doc_123",
      "page": 1,
      "path": "gs://bucket/file.pdf",
      "chunk_id": "chunk_456",
      "checksum": "abc789"
    }
  ]
}

※必ずJSON形式のみで回答してください。"""

    user_prompt = f"""質問: {query}

参考資料:
{context}

上記の参考資料に基づいて回答してください。cited_chunksには使用したチャンクの情報を必ず含めてください。"""

    # Use Vertex AI Gemini API
    import vertexai
    from vertexai.preview.generative_models import GenerativeModel
    from app.config import Config

    vertexai.init(project=Config.PROJECT_ID, location=Config.LOCATION)

    model = GenerativeModel(model_name)

    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    try:
        response = model.generate_content(
            full_prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "top_p": 0.95,
                "top_k": 40,
            }
        )

        response_text = response.text.strip()

        print("=== Gemini Response ===")
        print(response_text)
        print("=" * 50)

        # Extract JSON from response
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.rfind("```")
            response_text = response_text[start:end].strip()

        result = json.loads(response_text)

    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Failed to parse response: {response_text}")
        raise ValueError(f"Failed to parse JSON response from Gemini: {e}")
    except Exception as e:
        raise ValueError(f"Error calling Gemini API: {e}")

    answer = result.get("answer", "")
    cited_chunks = result.get("cited_chunks", [])

    print(f"Answer: {answer}")
    print(f"Cited chunks count: {len(cited_chunks)}")

    if not answer:
        raise ValueError("No answer generated")

    # cited_chunksが空の場合、全てのhitsをフォールバックとして使用
    if not cited_chunks:
        print("Warning: No citations from model, using all hits as fallback")
        cited_chunks = [
            {
                "doc_id": hit.doc_id,
                "page": hit.page,
                "path": hit.path,
                "chunk_id": hit.chunk_id,
                "checksum": hit.checksum
            }
            for hit in hits
        ]

    citations = []
    for cited_chunk in cited_chunks:
        citations.append(Citation(
            doc_id=cited_chunk["doc_id"],
            page=cited_chunk["page"],
            path=cited_chunk["path"],
            chunk_id=cited_chunk["chunk_id"],
            checksum=cited_chunk["checksum"]
        ))

    return answer, citations



def format_context_for_prompt(hits: List[ChunkHit]) -> str:
    """
    Format context chunks for prompt.
    
    Args:
        hits: List of ChunkHit objects
        
    Returns:
        Formatted context string
    """
    context_parts = []
    
    for i, hit in enumerate(hits, 1):
        full_text = hit.full_text if hit.full_text else hit.preview_text
        
        context_part = f"""[チャンク {i}]
ドキュメント: {hit.doc_id}
ページ: {hit.page}
パス: {hit.path}
チャンクID: {hit.chunk_id}
チェックサム: {hit.checksum}
内容:
{full_text}

---"""
        context_parts.append(context_part)
    
    return "\n".join(context_parts)


async def generate_answer_with_retry(
    query: str,
    hits: List[ChunkHit],
    max_retries: int = 2,
    **kwargs
) -> Tuple[str, List[Citation]]:
    """
    Generate answer with retry logic for citation failures.
    
    Args:
        query: User query
        hits: List of relevant chunk hits
        max_retries: Maximum number of retry attempts
        **kwargs: Additional arguments for generate_answer
        
    Returns:
        Tuple of (answer, citations)
        
    Raises:
        ValueError: If all retry attempts fail
    """
    for attempt in range(max_retries + 1):
        try:
            return generate_answer(query, hits, **kwargs)
        except ValueError as e:
            if attempt == max_retries:
                raise ValueError(f"Failed to generate answer with citations after {max_retries + 1} attempts: {str(e)}")
            
            continue