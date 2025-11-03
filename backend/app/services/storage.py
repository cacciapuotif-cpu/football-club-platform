"""
S3/MinIO Storage Service with retry and presigned URLs.
Production-ready file storage abstraction.
"""

import logging
import os
from datetime import timedelta
from pathlib import Path
from typing import BinaryIO, Optional
from urllib.parse import urlparse

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    Storage service supporting S3/MinIO with fallback to local filesystem.
    """

    def __init__(self):
        self.backend = settings.STORAGE_BACKEND
        self.local_path = Path(settings.STORAGE_LOCAL_PATH)

        if self.backend == "s3":
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path" if "minio" in settings.S3_ENDPOINT_URL else "auto"},
                ),
            )
            self.bucket = settings.S3_BUCKET
            self._ensure_bucket()
        else:
            self.s3_client = None
            self.local_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Storage initialized: backend={self.backend}")

    def _ensure_bucket(self):
        """Ensure S3 bucket exists."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
            logger.info(f"Bucket {self.bucket} exists")
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.warning(f"Bucket {self.bucket} not found, creating...")
                self.s3_client.create_bucket(Bucket=self.bucket)
                logger.info(f"Bucket {self.bucket} created")
            else:
                raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def upload_file(
        self,
        file: BinaryIO,
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload file to storage.
        Returns: public URL or presigned URL.
        """
        if self.backend == "s3":
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type
            if metadata:
                extra_args["Metadata"] = metadata

            self.s3_client.upload_fileobj(file, self.bucket, key, ExtraArgs=extra_args)
            logger.info(f"Uploaded {key} to S3 bucket {self.bucket}")
            return self.get_url(key)
        else:
            # Local filesystem
            dest_path = self.local_path / key
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(file.read())
            logger.info(f"Uploaded {key} to local storage")
            return f"/storage/{key}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def download_file(self, key: str, dest: BinaryIO):
        """Download file from storage."""
        if self.backend == "s3":
            self.s3_client.download_fileobj(self.bucket, key, dest)
            logger.info(f"Downloaded {key} from S3")
        else:
            src_path = self.local_path / key
            if not src_path.exists():
                raise FileNotFoundError(f"File not found: {key}")
            with open(src_path, "rb") as f:
                dest.write(f.read())
            logger.info(f"Downloaded {key} from local storage")

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Get presigned URL for file access.
        """
        if self.backend == "s3":
            try:
                url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": key},
                    ExpiresIn=expires_in,
                )
                return url
            except ClientError as e:
                logger.error(f"Failed to generate presigned URL for {key}: {e}")
                raise
        else:
            return f"/storage/{key}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def delete_file(self, key: str):
        """Delete file from storage."""
        if self.backend == "s3":
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted {key} from S3")
        else:
            file_path = self.local_path / key
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted {key} from local storage")

    def list_files(self, prefix: str = "") -> list[str]:
        """List files in storage with given prefix."""
        if self.backend == "s3":
            response = self.s3_client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            return [obj["Key"] for obj in response.get("Contents", [])]
        else:
            search_path = self.local_path / prefix if prefix else self.local_path
            if not search_path.exists():
                return []
            return [str(p.relative_to(self.local_path)) for p in search_path.rglob("*") if p.is_file()]


# Global singleton
storage_service = StorageService()
