"""File storage service with S3 and local filesystem support."""

import json
import logging
import os
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from bookbrain.core.config import settings

logger = logging.getLogger(__name__)

CHUNK_SIZE = 64 * 1024  # 64KB chunks for streaming


def get_s3_client():
    """Create and return an S3 client for Oracle Object Storage."""
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
    )


async def save_file_to_s3(file: UploadFile) -> str:
    """
    Upload file to S3 (Oracle Object Storage).

    Args:
        file: The uploaded file

    Returns:
        The S3 object key (path in bucket)

    Raises:
        ClientError: If upload fails
    """
    file_id = str(uuid.uuid4())
    object_key = f"pdfs/{file_id}.pdf"

    s3_client = get_s3_client()

    # Read file content
    content = await file.read()
    await file.seek(0)  # Reset for potential re-reads

    try:
        s3_client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=object_key,
            Body=content,
            ContentType="application/pdf",
        )
        logger.info(f"Uploaded file to S3: {object_key}")
        return f"s3://{settings.s3_bucket_name}/{object_key}"
    except ClientError as e:
        logger.error(f"Failed to upload to S3: {e}")
        raise


async def save_file_to_local(file: UploadFile) -> str:
    """
    Save uploaded file to local disk using streaming.

    Args:
        file: The uploaded file

    Returns:
        The path to the saved file
    """
    storage_dir = Path(settings.pdf_storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    file_path = storage_dir / f"{file_id}.pdf"

    # Stream file to disk in chunks
    with open(file_path, "wb") as f:
        while chunk := await file.read(CHUNK_SIZE):
            f.write(chunk)

    logger.info(f"Saved file to local: {file_path}")
    return str(file_path)


async def save_uploaded_file(file: UploadFile) -> str:
    """
    Save uploaded file to storage (S3 or local based on configuration).

    Args:
        file: The uploaded file

    Returns:
        The storage path (S3 URI or local path)
    """
    if settings.s3_enabled:
        return await save_file_to_s3(file)
    else:
        return await save_file_to_local(file)


def delete_file_from_s3(file_path: str) -> bool:
    """
    Delete file from S3.

    Args:
        file_path: S3 URI (s3://bucket/key)

    Returns:
        True if deleted successfully
    """
    if not file_path.startswith("s3://"):
        return False

    # Parse S3 URI: s3://bucket/key
    path_parts = file_path[5:].split("/", 1)
    if len(path_parts) != 2:
        return False

    bucket_name, object_key = path_parts

    s3_client = get_s3_client()

    try:
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        logger.info(f"Deleted file from S3: {object_key}")
        return True
    except ClientError as e:
        logger.error(f"Failed to delete from S3: {e}")
        return False


def delete_file_from_local(file_path: str) -> bool:
    """
    Delete file from local disk.

    Args:
        file_path: Local file path

    Returns:
        True if deleted successfully
    """
    if not os.path.exists(file_path):
        return False

    try:
        os.remove(file_path)
        logger.info(f"Deleted file from local: {file_path}")
        return True
    except OSError as e:
        logger.error(f"Failed to delete local file: {e}")
        return False


def delete_stored_file(file_path: str) -> bool:
    """
    Delete file from storage (S3 or local based on path).

    Args:
        file_path: The storage path (S3 URI or local path)

    Returns:
        True if deleted successfully
    """
    if file_path.startswith("s3://"):
        return delete_file_from_s3(file_path)
    else:
        return delete_file_from_local(file_path)


# =============================================================================
# JSON Storage (for Storm Parse results)
# =============================================================================


def save_parsed_result_to_s3(book_id: int, response_data: dict[str, Any]) -> str | None:
    """
    Save Storm Parse API response to S3 as JSON.

    Args:
        book_id: The book ID for naming the file
        response_data: The raw Storm Parse API response

    Returns:
        The S3 URI if successful, None if failed or S3 disabled
    """
    if not settings.s3_enabled:
        logger.debug("S3 disabled, skipping parsed result storage")
        return None

    object_key = f"parsed/{book_id}.json"
    s3_client = get_s3_client()

    try:
        json_content = json.dumps(response_data, ensure_ascii=False, indent=2)
        s3_client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=object_key,
            Body=json_content.encode("utf-8"),
            ContentType="application/json",
        )
        s3_uri = f"s3://{settings.s3_bucket_name}/{object_key}"
        logger.info(f"Saved parsed result to S3: {object_key}")
        return s3_uri
    except ClientError as e:
        logger.error(f"Failed to save parsed result to S3: {e}")
        return None
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize parsed result to JSON: {e}")
        return None


def load_parsed_result_from_s3(book_id: int) -> dict[str, Any] | None:
    """
    Load Storm Parse API response from S3.

    Args:
        book_id: The book ID to load

    Returns:
        The parsed result dict if successful, None if not found or failed
    """
    if not settings.s3_enabled:
        logger.debug("S3 disabled, cannot load parsed result")
        return None

    object_key = f"parsed/{book_id}.json"
    s3_client = get_s3_client()

    try:
        response = s3_client.get_object(
            Bucket=settings.s3_bucket_name,
            Key=object_key,
        )
        content = response["Body"].read().decode("utf-8")
        result = json.loads(content)
        logger.info(f"Loaded parsed result from S3: {object_key}")
        return result
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code in ("NoSuchKey", "404"):
            logger.debug(f"Parsed result not found in S3: {object_key}")
        else:
            logger.error(f"Failed to load parsed result from S3: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from S3: {e}")
        return None


def delete_parsed_result_from_s3(book_id: int) -> bool:
    """
    Delete Storm Parse result from S3.

    Args:
        book_id: The book ID

    Returns:
        True if deleted successfully or not found
    """
    if not settings.s3_enabled:
        return True

    object_key = f"parsed/{book_id}.json"
    s3_client = get_s3_client()

    try:
        s3_client.delete_object(
            Bucket=settings.s3_bucket_name,
            Key=object_key,
        )
        logger.info(f"Deleted parsed result from S3: {object_key}")
        return True
    except ClientError as e:
        logger.error(f"Failed to delete parsed result from S3: {e}")
        return False


# =============================================================================
# S3 File Download (for parsing S3-stored PDFs)
# =============================================================================


@contextmanager
def download_from_s3_to_temp(s3_uri: str):
    """
    Download file from S3 to a temporary file.

    Usage:
        with download_from_s3_to_temp("s3://bucket/key") as temp_path:
            # Use temp_path
        # File is automatically deleted after the block

    Args:
        s3_uri: S3 URI (s3://bucket/key)

    Yields:
        Path to the temporary file

    Raises:
        ClientError: If download fails
        ValueError: If S3 URI is invalid
    """
    if not s3_uri.startswith("s3://"):
        raise ValueError(f"Invalid S3 URI: {s3_uri}")

    # Parse S3 URI: s3://bucket/key
    path_parts = s3_uri[5:].split("/", 1)
    if len(path_parts) != 2:
        raise ValueError(f"Invalid S3 URI format: {s3_uri}")

    bucket_name, object_key = path_parts

    # Determine file extension
    suffix = Path(object_key).suffix or ".tmp"

    s3_client = get_s3_client()
    temp_file = None

    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()

        # Download from S3
        s3_client.download_file(bucket_name, object_key, str(temp_path))
        logger.info(f"Downloaded S3 file to temp: {s3_uri} -> {temp_path}")

        yield temp_path

    finally:
        # Cleanup temporary file
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.remove(temp_file.name)
                logger.debug(f"Cleaned up temp file: {temp_file.name}")
            except OSError as e:
                logger.warning(f"Failed to cleanup temp file: {e}")
