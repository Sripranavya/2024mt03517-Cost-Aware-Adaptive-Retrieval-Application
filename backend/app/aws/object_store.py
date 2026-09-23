"""Object stores: local filesystem (local) and Amazon S3 (cloud).

Blob storage for corpus artifacts and the persisted vector index. The local
store writes under a base directory; the S3 store uses the default credential
chain with the bucket name injected from settings.
"""

from __future__ import annotations

from pathlib import Path

from app.aws.interfaces import ObjectStore


class LocalObjectStore(ObjectStore):
    """Filesystem-backed object store rooted at ``base_dir``."""

    def __init__(self, base_dir: str) -> None:
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        # Prevent path traversal outside the base directory.
        target = (self.base / key).resolve()
        if not str(target).startswith(str(self.base.resolve())):
            raise ValueError("object key escapes the storage root")
        return target

    def put_bytes(self, key: str, data: bytes) -> None:
        target = self._resolve(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def get_bytes(self, key: str) -> bytes | None:
        target = self._resolve(key)
        return target.read_bytes() if target.exists() else None

    def exists(self, key: str) -> bool:
        return self._resolve(key).exists()


class S3ObjectStore(ObjectStore):
    """Amazon S3 object store (cloud mode)."""

    def __init__(self, bucket_name: str, region: str) -> None:
        if not bucket_name:
            raise ValueError("S3 bucket name is required in cloud mode")
        import boto3  # lazy import

        self.bucket = bucket_name
        self._client = boto3.client("s3", region_name=region)

    def put_bytes(self, key: str, data: bytes) -> None:
        self._client.put_object(Bucket=self.bucket, Key=key, Body=data)

    def get_bytes(self, key: str) -> bytes | None:
        try:
            response = self._client.get_object(Bucket=self.bucket, Key=key)
        except self._client.exceptions.NoSuchKey:
            return None
        return response["Body"].read()

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False
