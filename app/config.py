import os
from typing import Optional
from google.cloud import aiplatform
from dotenv import load_dotenv

load_dotenv()


class Config:
    PROJECT_ID: Optional[str] = os.getenv("PROJECT_ID")
    LOCATION: str = os.getenv("LOCATION", "asia-northeast1")
    BUCKET_NAME: Optional[str] = os.getenv("BUCKET_NAME")
    INDEX_ID: Optional[str] = os.getenv("INDEX_ID")
    INDEX_ENDPOINT_ID: Optional[str] = os.getenv("INDEX_ENDPOINT_ID")
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values."""
        required_vars = {
            "PROJECT_ID": cls.PROJECT_ID,
            "BUCKET_NAME": cls.BUCKET_NAME,
            "INDEX_ID": cls.INDEX_ID,
            "INDEX_ENDPOINT_ID": cls.INDEX_ENDPOINT_ID
        }
        
        missing_vars = [name for name, value in required_vars.items() if not value]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    @classmethod
    def initialize_aiplatform(cls) -> None:
        """Initialize Vertex AI platform."""
        cls.validate()
        aiplatform.init(project=cls.PROJECT_ID, location=cls.LOCATION)