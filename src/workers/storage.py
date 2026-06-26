import io
import logging
from pathlib import Path
from typing import BinaryIO, Optional

from src.config import settings

logger = logging.getLogger(__name__)


class StorageClient:
    """
    Unified Storage client providing transparent switching between AWS S3 buckets
    and local filesystem mock storage for document ingestion workers.
    """

    def __init__(self):
        self.use_mock = settings.use_mock_s3
        self.bucket = settings.aws_s3_bucket
        self.local_dir = settings.get_storage_path()
        self._s3_client = None

    @property
    def s3(self):
        if not self.use_mock and self._s3_client is None:
            import boto3
            self._s3_client = boto3.client(
                "s3",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
        return self._s3_client

    def save_document(self, filename: str, content: bytes) -> str:
        """
        Store raw document bytes into target storage bucket/directory.
        Returns URI or local path string.
        """
        if self.use_mock:
            target_path = self.local_dir / filename
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "wb") as f:
                f.write(content)
            logger.debug(f"Saved mock S3 file locally: {target_path}")
            return f"file://{target_path.resolve()}"

        try:
            self.s3.put_object(Bucket=self.bucket, Key=filename, Body=content)
            uri = f"s3://{self.bucket}/{filename}"
            logger.info(f"Uploaded document to AWS S3: {uri}")
            return uri
        except Exception as e:
            logger.error(f"AWS S3 put_object failed: {e}")
            raise

    def get_document_stream(self, uri_or_filename: str) -> io.BytesIO:
        """
        Fetch document bytes from storage and return as in-memory stream.
        """
        if self.use_mock or uri_or_filename.startswith("file://"):
            if uri_or_filename.startswith("file://"):
                path = Path(uri_or_filename.replace("file://", ""))
            else:
                path = self.local_dir / uri_or_filename

            if not path.exists():
                raise FileNotFoundError(f"Document not found in local mock S3 storage: {path}")

            with open(path, "rb") as f:
                return io.BytesIO(f.read())

        key = uri_or_filename.replace(f"s3://{self.bucket}/", "")
        response = self.s3.get_object(Bucket=self.bucket, Key=key)
        return io.BytesIO(response["Body"].read())


storage_client = StorageClient()
