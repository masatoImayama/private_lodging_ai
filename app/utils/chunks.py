from typing import List
from app.schemas.dto import Chunk, PageText
from app.utils.hash import calculate_checksum


def make_chunks(
    pages: List[PageText],
    size: int = 1400,
    overlap: int = 160
) -> List[Chunk]:
    """
    Split pages into chunks with overlap.
    
    Args:
        pages: List of PageText objects
        size: Chunk size in characters
        overlap: Overlap size in characters
        
    Returns:
        List of Chunk objects
    """
    chunks = []
    chunk_counter = 0
    
    for page_text in pages:
        text = page_text.text
        page_num = page_text.page_num
        
        if len(text) <= size:
            chunk_id = f"c-{chunk_counter:05d}"
            chunk = Chunk(
                chunk_id=chunk_id,
                text=text,
                page=page_num,
                checksum=calculate_checksum(text),
                preview_text=text[:200]
            )
            chunks.append(chunk)
            chunk_counter += 1
        else:
            start = 0
            while start < len(text):
                end = min(start + size, len(text))
                chunk_text = text[start:end]
                
                chunk_id = f"c-{chunk_counter:05d}"
                chunk = Chunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    page=page_num,
                    checksum=calculate_checksum(chunk_text),
                    preview_text=chunk_text[:200]
                )
                chunks.append(chunk)
                chunk_counter += 1
                
                start += size - overlap
                if start >= len(text):
                    break
    
    return chunks