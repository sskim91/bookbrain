#!/usr/bin/env python3
"""S3 migration: sync local files to S3."""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from bookbrain.core.config import settings

# Default concurrency for parallel uploads
DEFAULT_PARALLEL = 4
MAX_PARALLEL = 10

# Thread-safe print lock
_print_lock = Lock()


def get_s3_client():
    """Get S3 client configured for Oracle Object Storage."""
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
    )


def list_local_files(local_dir: Path, pattern: str = "*") -> list[Path]:
    """List files in local directory.

    Args:
        local_dir: Local directory path
        pattern: Glob pattern for files

    Returns:
        List of file paths
    """
    if not local_dir.exists():
        return []
    return sorted(local_dir.glob(pattern))


def list_s3_keys(s3_client, prefix: str) -> set[str]:
    """List keys in S3 bucket with prefix.

    Args:
        s3_client: Boto3 S3 client
        prefix: Key prefix to list

    Returns:
        Set of key names (without prefix)
    """
    keys = set()
    paginator = s3_client.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=settings.s3_bucket_name, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            # Remove prefix to get just the filename
            name = key[len(prefix):].lstrip("/")
            if name:
                keys.add(name)

    return keys


def _safe_print(msg: str, end: str = "\n") -> None:
    """Thread-safe print function."""
    with _print_lock:
        print(msg, end=end, flush=True)


@dataclass
class UploadResult:
    """Result of a single file upload."""

    filename: str
    status: str  # "uploaded", "skipped", "failed"
    error: str | None = None


def _upload_single_file(
    s3_client,
    file_path: Path,
    s3_prefix: str,
    existing_keys: set[str],
    dry_run: bool,
) -> UploadResult:
    """Upload a single file to S3.

    Args:
        s3_client: Boto3 S3 client
        file_path: Local file path
        s3_prefix: S3 prefix (folder)
        existing_keys: Set of existing S3 keys
        dry_run: If True, don't actually upload

    Returns:
        UploadResult with status
    """
    from botocore.exceptions import ClientError

    filename = file_path.name
    s3_key = f"{s3_prefix}/{filename}"

    if filename in existing_keys:
        _safe_print(f"  \033[33m○ Skip:\033[0m {filename} (already exists)")
        return UploadResult(filename=filename, status="skipped")

    if dry_run:
        _safe_print(f"  \033[34m→ Would upload:\033[0m {filename}")
        return UploadResult(filename=filename, status="uploaded")

    try:
        file_size = file_path.stat().st_size
        _safe_print(f"  \033[34m↑ Uploading:\033[0m {filename} ({file_size:,} bytes)...")

        s3_client.upload_file(str(file_path), settings.s3_bucket_name, s3_key)

        _safe_print(f"  \033[32m✓ Done:\033[0m {filename}")
        return UploadResult(filename=filename, status="uploaded")
    except ClientError as e:
        _safe_print(f"  \033[31m✗ Failed:\033[0m {filename} - {e}")
        return UploadResult(filename=filename, status="failed", error=str(e))
    except Exception as e:
        _safe_print(f"  \033[31m✗ Failed:\033[0m {filename} - {e}")
        return UploadResult(filename=filename, status="failed", error=str(e))


def sync_to_s3(
    local_dir: Path,
    s3_prefix: str,
    dry_run: bool = False,
    pattern: str = "*",
    parallel: int = 1,
) -> tuple[int, int, int]:
    """Sync local directory to S3.

    Args:
        local_dir: Local directory to sync
        s3_prefix: S3 prefix (folder) to sync to
        dry_run: If True, don't actually upload
        pattern: Glob pattern for files
        parallel: Number of concurrent uploads (1 = sequential)

    Returns:
        Tuple of (uploaded, skipped, failed) counts
    """
    s3 = get_s3_client()

    # Get existing keys in S3
    existing_keys = list_s3_keys(s3, s3_prefix)
    print(f"  Found {len(existing_keys)} existing files in S3")

    # Get local files
    local_files = list_local_files(local_dir, pattern)
    print(f"  Found {len(local_files)} local files")

    if not local_files:
        return 0, 0, 0

    uploaded = 0
    skipped = 0
    failed = 0

    if parallel > 1:
        print(f"  Using {parallel} parallel uploads")
        # Parallel upload using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {
                executor.submit(
                    _upload_single_file, s3, file_path, s3_prefix, existing_keys, dry_run
                ): file_path
                for file_path in local_files
            }

            for future in as_completed(futures):
                result = future.result()
                if result.status == "uploaded":
                    uploaded += 1
                elif result.status == "skipped":
                    skipped += 1
                else:
                    failed += 1
    else:
        # Sequential upload (original behavior)
        for file_path in local_files:
            result = _upload_single_file(s3, file_path, s3_prefix, existing_keys, dry_run)
            if result.status == "uploaded":
                uploaded += 1
            elif result.status == "skipped":
                skipped += 1
            else:
                failed += 1

    return uploaded, skipped, failed


def main() -> int:
    """Main entry point for S3 sync."""
    parser = argparse.ArgumentParser(description="Sync local files to S3")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without actually syncing",
    )
    parser.add_argument(
        "--pdfs-only",
        action="store_true",
        help="Only sync PDF files",
    )
    parser.add_argument(
        "--parsed-only",
        action="store_true",
        help="Only sync parsed results",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=DEFAULT_PARALLEL,
        help=f"Number of parallel uploads (default: {DEFAULT_PARALLEL}, max: {MAX_PARALLEL})",
    )

    args = parser.parse_args()

    # Validate parallel option
    if args.parallel < 1:
        args.parallel = 1
    elif args.parallel > MAX_PARALLEL:
        print(f"\033[33mWarning: Limiting parallel uploads to {MAX_PARALLEL}\033[0m")
        args.parallel = MAX_PARALLEL

    # Check if S3 is enabled
    if not settings.s3_enabled:
        print("\n\033[33mWarning: S3 is not enabled\033[0m")
        print("Set S3_ENABLED=true and configure S3_* environment variables.")
        return 1

    # Check credentials
    if not settings.s3_endpoint_url or not settings.s3_access_key:
        print("\n\033[31mError: S3 credentials not configured\033[0m")
        print("Required environment variables:")
        print("  S3_ENDPOINT_URL, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET_NAME")
        return 1

    try:
        import boto3
    except ImportError:
        print("\n\033[31mError: boto3 not installed\033[0m")
        print("Install with: pip install boto3")
        return 1

    print("\n\033[34m=== S3 Sync ===\033[0m\n")
    print(f"Bucket: {settings.s3_bucket_name}")
    print(f"Endpoint: {settings.s3_endpoint_url}")

    if args.dry_run:
        print("\n\033[33m[DRY RUN] No files will be uploaded\033[0m")

    total_uploaded = 0
    total_skipped = 0
    total_failed = 0

    # Sync PDFs
    if not args.parsed_only:
        pdf_dir = Path(settings.pdf_storage_dir)
        print(f"\n\033[34mSyncing PDFs from {pdf_dir}...\033[0m")

        if pdf_dir.exists():
            uploaded, skipped, failed = sync_to_s3(
                pdf_dir,
                "pdfs",
                dry_run=args.dry_run,
                pattern="*.pdf",
                parallel=args.parallel,
            )
            total_uploaded += uploaded
            total_skipped += skipped
            total_failed += failed
        else:
            print(f"  \033[33mDirectory not found: {pdf_dir}\033[0m")

    # Sync parsed results
    if not args.pdfs_only:
        parsed_dir = Path(settings.data_dir) / "parsed"
        print(f"\n\033[34mSyncing parsed results from {parsed_dir}...\033[0m")

        if parsed_dir.exists():
            uploaded, skipped, failed = sync_to_s3(
                parsed_dir,
                "parsed",
                dry_run=args.dry_run,
                pattern="*.json",
                parallel=args.parallel,
            )
            total_uploaded += uploaded
            total_skipped += skipped
            total_failed += failed
        else:
            print(f"  \033[33mDirectory not found: {parsed_dir}\033[0m")

    # Summary
    print(f"\n\033[34m=== Summary ===\033[0m")
    if args.dry_run:
        print(f"  Would upload: {total_uploaded}")
    else:
        print(f"  Uploaded: {total_uploaded}")
    print(f"  Skipped: {total_skipped}")
    if total_failed > 0:
        print(f"  \033[31mFailed: {total_failed}\033[0m")

    print()

    return 1 if total_failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
