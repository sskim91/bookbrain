#!/usr/bin/env python3
"""Status check for all migration services."""

import argparse
import sys
from urllib.parse import urlparse

import httpx

from bookbrain.core.config import settings


def check_postgresql() -> tuple[bool, str]:
    """Check PostgreSQL connection status."""
    try:
        import psycopg

        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.execute("SELECT COUNT(*) FROM books")
                book_count = cur.fetchone()[0]
        return True, f"Connected ({book_count} books)"
    except ImportError:
        return False, "psycopg not installed"
    except Exception as e:
        return False, str(e)


def check_qdrant() -> tuple[bool, str]:
    """Check Qdrant connection status."""
    try:
        url = f"{settings.qdrant_url}/collections/{settings.qdrant_collection}"
        response = httpx.get(url, timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            points_count = data.get("result", {}).get("points_count", 0)
            return True, f"Connected ({points_count} points)"
        return False, f"HTTP {response.status_code}"
    except httpx.ConnectError:
        return False, "Connection refused"
    except Exception as e:
        return False, str(e)


def check_s3() -> tuple[bool, str]:
    """Check S3 connection status."""
    if not settings.s3_enabled:
        return True, "Disabled (using local storage)"

    if not settings.s3_endpoint_url:
        return False, "S3_ENDPOINT_URL not configured"

    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError

        s3 = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )

        # Try to list objects (limit 1) to verify access
        response = s3.list_objects_v2(
            Bucket=settings.s3_bucket_name,
            MaxKeys=1,
        )
        key_count = response.get("KeyCount", 0)
        return True, f"Connected (bucket: {settings.s3_bucket_name})"
    except ImportError:
        return False, "boto3 not installed"
    except NoCredentialsError:
        return False, "Invalid credentials"
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        return False, f"S3 error: {error_code}"
    except Exception as e:
        return False, str(e)


def print_status(name: str, ok: bool, message: str) -> None:
    """Print service status with color coding."""
    status = "\033[32m✓\033[0m" if ok else "\033[31m✗\033[0m"
    color = "\033[32m" if ok else "\033[31m"
    reset = "\033[0m"
    print(f"  {status} {name}: {color}{message}{reset}")


def main() -> int:
    """Run status checks for all services."""
    parser = argparse.ArgumentParser(description="Check migration service status")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output status in JSON format",
    )
    args = parser.parse_args()

    print("\n=== BookBrain Migration Status ===\n")

    all_ok = True

    # PostgreSQL
    pg_ok, pg_msg = check_postgresql()
    print_status("PostgreSQL", pg_ok, pg_msg)
    if not pg_ok:
        all_ok = False

    # Qdrant
    qdrant_ok, qdrant_msg = check_qdrant()
    print_status("Qdrant", qdrant_ok, qdrant_msg)
    if not qdrant_ok:
        all_ok = False

    # S3
    s3_ok, s3_msg = check_s3()
    print_status("S3", s3_ok, s3_msg)
    if not s3_ok and settings.s3_enabled:
        all_ok = False

    print()

    if all_ok:
        print("\033[32mAll services are available.\033[0m")
    else:
        print("\033[31mSome services are unavailable.\033[0m")
        print("\nTroubleshooting:")
        if not pg_ok:
            print("  - Check DATABASE_URL environment variable")
            print("  - Verify PostgreSQL is running: docker-compose ps")
        if not qdrant_ok:
            print("  - Check QDRANT_URL environment variable")
            print("  - Verify Qdrant is running: docker-compose ps")
        if not s3_ok and settings.s3_enabled:
            print("  - Check S3_* environment variables")
            print("  - Verify S3 credentials and bucket access")

    print()
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
