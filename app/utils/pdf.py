import os
import tempfile
from typing import List
from google.cloud import storage
from pypdf import PdfReader
from app.schemas.dto import PageText


def extract_text_from_pdf(gcs_uri: str) -> List[PageText]:
    """
    Extract text from a PDF or text file stored in GCS.

    Args:
        gcs_uri: GCS URI of the file (gs://bucket/path/to/file.pdf or .txt)

    Returns:
        List of PageText objects containing text from each page

    Raises:
        ValueError: If the GCS URI is invalid
        Exception: If extraction fails
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
    file_extension = blob_name.lower().split('.')[-1] if '.' in blob_name else ''

    # Handle text files
    if file_extension in ['txt', 'text', 'md']:
        content = blob.download_as_text(encoding='utf-8')
        # Split content into pages by double newline or fixed size
        # For simplicity, treat entire content as one page for text files
        if content:
            pages.append(PageText(
                page_num=1,
                text=content.strip()
            ))
    # Handle PDF files
    else:
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
        raise ValueError(f"No text could be extracted from file: {gcs_uri}")

    return pages