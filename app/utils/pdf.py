import os
import tempfile
from typing import List
from google.cloud import storage
from pypdf import PdfReader
from app.schemas.dto import PageText


def extract_text_from_pdf(gcs_uri: str) -> List[PageText]:
    """
    Extract text from a PDF file stored in GCS.
    
    Args:
        gcs_uri: GCS URI of the PDF file (gs://bucket/path/to/file.pdf)
        
    Returns:
        List of PageText objects containing text from each page
        
    Raises:
        ValueError: If the GCS URI is invalid
        Exception: If PDF extraction fails
    """
    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS URI: {gcs_uri}")
    
    parts = gcs_uri[5:].split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid GCS URI format: {gcs_uri}")
    
    bucket_name, blob_name = parts
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    if not blob.exists():
        raise ValueError(f"File not found: {gcs_uri}")
    
    pages = []
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        blob.download_to_filename(tmp_path)
        
        reader = PdfReader(tmp_path)
        
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text:
                pages.append(PageText(
                    page_num=page_num,
                    text=text.strip()
                ))
    finally:
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except:
            pass
    
    if not pages:
        raise ValueError(f"No text could be extracted from PDF: {gcs_uri}")
    
    return pages