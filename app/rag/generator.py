import json
from typing import List, Tuple
from google.cloud import aiplatform
from app.schemas.dto import ChunkHit, Citation


def generate_answer(
    query: str,
    hits: List[ChunkHit],
    model_name: str = "gemini-1.5-pro",
    temperature: float = 0.3,
    max_tokens: int = 800
) -> Tuple[str, List[Citation]]:
    """
    Generate answer using Gemini with mandatory citations.
    
    Args:
        query: User query
        hits: List of relevant chunk hits
        model_name: Name of the generation model
        temperature: Generation temperature
        max_tokens: Maximum number of tokens
        
    Returns:
        Tuple of (answer, citations)
    """
    if not hits:
        raise ValueError("No context chunks provided for answer generation")
    
    context = format_context_for_prompt(hits)
    
    system_prompt = """あなたは社内ドキュメントに基づいて回答するアシスタントです。
回答は登録文書の根拠に厳密に依拠してください。根拠が不十分な場合は「不明」と述べ、想像で補完しないでください。
出力には、回答本文に加えて参照したチャンクの {doc_id, page, path, chunk_id, checksum} を必ず含めます。

出力は必ず以下のJSON形式で返してください：
{
  "answer": "ここに回答本文を記載",
  "cited_chunks": [
    {
      "doc_id": "ドキュメントID",
      "page": ページ番号,
      "path": "GCSパス",
      "chunk_id": "チャンクID",
      "checksum": "チェックサム"
    }
  ]
}

必ず cited_chunks には実際に参照したチャンクのみを含めてください。"""
    
    user_prompt = f"""質問: {query}

参考資料:
{context}

上記の参考資料に基づいて回答してください。必ず引用したソースを明記してください。"""
    
    # Use actual Vertex AI Gemini API
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
            }
        )

        # Parse JSON response
        response_text = response.text.strip()

        # Extract JSON from response if wrapped in markdown
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
        raise ValueError(f"Failed to parse JSON response from Gemini: {e}")
    except Exception as e:
        raise ValueError(f"Error calling Gemini API: {e}")

    answer = result.get("answer", "")
    cited_chunks = result.get("cited_chunks", [])

    if not answer:
        raise ValueError("No answer generated")

    if not cited_chunks:
        raise ValueError("No citations provided in the generated answer")

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