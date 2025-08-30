import hashlib


def calculate_checksum(text: str) -> str:
    """
    Calculate SHA256 checksum for the given text.
    
    Args:
        text: Input text to hash
        
    Returns:
        SHA256 hash as hex string
    """
    return f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"