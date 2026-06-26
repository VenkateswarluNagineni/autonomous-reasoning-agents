import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Enterprise Application Settings loaded from environment variables or .env file.
    """
    app_env: str = "production"
    api_port: int = 8000
    debug: bool = False

    # Redis & RQ Infrastructure
    redis_url: str = "redis://localhost:6379/0"
    rq_queue_name: str = "document_ingestion"

    # RAG Memory
    embedding_model_name: str = "all-MiniLM-L6-v2"
    vector_index_path: str = "./data/vector_store.index"
    vector_dimension: int = 384

    # AWS Storage
    aws_region: str = "us-east-1"
    aws_access_key_id: str = "mock_key"
    aws_secret_access_key: str = "mock_secret"
    aws_s3_bucket: str = "enterprise-document-ingestion-corpus"
    use_mock_s3: bool = True
    local_storage_dir: str = "./data/raw_documents"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_storage_path(self) -> Path:
        p = Path(self.local_storage_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
