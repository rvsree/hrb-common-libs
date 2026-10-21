"""Generic S3 operations - new, parameterized code (see ROADMAP.md's Phase 6 scope
note: hrb_chatbot_v2's s3_upload_client.py mixes a generic presigned-URL operation
with leave-document/admin-doc business logic and hardcoded bucket env var names -
only the generic operation, parameterized by bucket, belongs here)."""

import boto3

from hrb_common.observability.call_logger import log_backend_call
from hrb_common.observability.logger import get_logger

logger = get_logger("s3_client")

DEFAULT_REGION = "us-east-1"
DEFAULT_EXPIRY_SECONDS = 300


def generate_presigned_upload_url(bucket: str, key: str, content_type: str, expiry_seconds: int = DEFAULT_EXPIRY_SECONDS, region: str = DEFAULT_REGION) -> dict:
    s3_client = boto3.client("s3", region_name=region)
    with log_backend_call(logger, "s3", "generate_presigned_url", bucket=bucket, key=key):
        upload_url = s3_client.generate_presigned_url(
            "put_object", Params={"Bucket": bucket, "Key": key, "ContentType": content_type}, ExpiresIn=expiry_seconds
        )
    return {"upload_url": upload_url, "key": key, "expires_in_seconds": expiry_seconds}


def generate_presigned_download_url(bucket: str, key: str, expiry_seconds: int = DEFAULT_EXPIRY_SECONDS, region: str = DEFAULT_REGION) -> dict:
    s3_client = boto3.client("s3", region_name=region)
    with log_backend_call(logger, "s3", "generate_presigned_url", bucket=bucket, key=key):
        download_url = s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expiry_seconds
        )
    return {"download_url": download_url, "expires_in_seconds": expiry_seconds}


def delete_object(bucket: str, key: str, region: str = DEFAULT_REGION) -> None:
    """Best-effort - deleting an already-missing key is a no-op, not an error."""
    s3_client = boto3.client("s3", region_name=region)
    with log_backend_call(logger, "s3", "delete_object", bucket=bucket, key=key):
        s3_client.delete_object(Bucket=bucket, Key=key)
