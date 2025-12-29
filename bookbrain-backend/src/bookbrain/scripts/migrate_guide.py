#!/usr/bin/env python3
"""Migration guide: step-by-step instructions for data migration."""

import argparse
import sys

from bookbrain.core.config import settings


def print_guide() -> int:
    """Print the complete migration guide.

    Returns:
        Exit code (0 for success)
    """
    guide = """
\033[34m╔══════════════════════════════════════════════════════════════╗
║              BookBrain Migration Guide                        ║
╚══════════════════════════════════════════════════════════════╝\033[0m

This guide walks you through migrating BookBrain data from a local
development environment to a cloud/production environment.

\033[33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m
\033[34mPREREQUISITES\033[0m
\033[33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m

Before starting, ensure you have:

  [ ] PostgreSQL client tools (pg_dump, pg_restore)
      • macOS: brew install postgresql
      • Ubuntu: sudo apt install postgresql-client

  [ ] Python dependencies
      • boto3 for S3 operations
      • httpx for Qdrant API

  [ ] Target environment access
      • Target PostgreSQL connection URL
      • Target Qdrant URL
      • S3 credentials (if using S3 storage)

Check current status:
  $ ./scripts/migrate.sh status

\033[33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m
\033[34mSTEP 1: PostgreSQL Migration\033[0m
\033[33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m

1.1 Create a database dump from local PostgreSQL:

    $ ./scripts/migrate.sh dump
    # or specify output file:
    $ ./scripts/migrate.sh dump --output ./backup/bookbrain_$(date +%Y%m%d).sql

1.2 Restore the dump to target database:

    $ ./scripts/migrate.sh restore --target "postgresql://user:pass@host:5432/dbname"

    ⚠️  Warning: This will OVERWRITE existing data in the 'books' table.

1.3 Verify the migration:

    $ psql <target-url> -c "SELECT COUNT(*) FROM books;"

\033[33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m
\033[34mSTEP 2: Qdrant Vector Store Migration\033[0m
\033[33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m

\033[32mOption A: Snapshot Transfer (recommended for large collections)\033[0m

2a.1 Create a snapshot:
    $ ./scripts/migrate.sh snapshot

2a.2 Download the snapshot:
    $ ./scripts/migrate.sh snapshot --download ./backup/

2a.3 Transfer to target server and recover:
    # Copy snapshot file to target
    $ scp ./backup/<snapshot-name>.snapshot user@target:/path/to/

    # On target, use Qdrant API to recover:
    $ curl -X PUT "http://target-qdrant:6333/collections/chunks/snapshots/recover" \\
        -H "Content-Type: application/json" \\
        -d '{"location": "/path/to/<snapshot-name>.snapshot"}'

\033[32mOption B: Re-indexing (recommended for data integrity)\033[0m

If you have parsed results in S3, re-indexing is safer:

    $ python scripts/batch_upload.py --source <pdf-directory>

This rebuilds the vector index from source PDFs.

\033[33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m
\033[34mSTEP 3: S3 Storage Sync\033[0m
\033[33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m

3.1 Preview what will be synced (dry run):

    $ ./scripts/migrate.sh sync-s3 --dry-run

3.2 Sync local files to S3:

    $ ./scripts/migrate.sh sync-s3

    Files that already exist in S3 will be skipped.

3.3 Sync only specific file types:

    $ ./scripts/migrate.sh sync-s3 --pdfs-only
    $ ./scripts/migrate.sh sync-s3 --parsed-only

\033[33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m
\033[34mSTEP 4: Verification\033[0m
\033[33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m

4.1 Check all services on target:

    # Set target environment variables
    $ export DATABASE_URL="postgresql://..."
    $ export QDRANT_URL="http://..."
    $ export S3_ENABLED=true
    $ export S3_ENDPOINT_URL="..."

    $ ./scripts/migrate.sh status

4.2 Verify data counts:

    PostgreSQL:
    $ psql $DATABASE_URL -c "SELECT COUNT(*) FROM books;"

    Qdrant:
    $ curl $QDRANT_URL/collections/chunks | jq '.result.points_count'

4.3 Test search functionality:

    $ curl http://target:8000/api/search?q=test

\033[33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m
\033[34mTROUBLESHOOTING\033[0m
\033[33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m

\033[31mPostgreSQL connection failed\033[0m
  • Check DATABASE_URL format: postgresql://user:pass@host:5432/dbname
  • Verify network connectivity and firewall rules
  • Test with: psql $DATABASE_URL -c "SELECT 1"

\033[31mQdrant connection refused\033[0m
  • Check QDRANT_URL (default: http://localhost:6333)
  • Verify Qdrant container is running: docker-compose ps
  • Test with: curl $QDRANT_URL/collections

\033[31mS3 authentication failed\033[0m
  • Verify S3_ACCESS_KEY and S3_SECRET_KEY
  • Check S3_ENDPOINT_URL format for Oracle Object Storage
  • Ensure bucket exists and has proper permissions

\033[31mSnapshot recovery failed\033[0m
  • Ensure target collection doesn't exist, or use --overwrite
  • Check disk space on target server
  • Verify snapshot file integrity

\033[33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m
\033[34mQUICK REFERENCE\033[0m
\033[33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m

  Status check:     ./scripts/migrate.sh status
  Full guide:       ./scripts/migrate.sh guide
  Help:             ./scripts/migrate.sh help

  PostgreSQL:       ./scripts/migrate.sh dump
                    ./scripts/migrate.sh restore --target <url>

  Qdrant:           ./scripts/migrate.sh snapshot
                    ./scripts/migrate.sh snapshot --download ./backup/

  S3:               ./scripts/migrate.sh sync-s3 [--dry-run]

"""
    print(guide)
    return 0


def main() -> int:
    """Main entry point for migration guide."""
    parser = argparse.ArgumentParser(description="Show migration guide")
    parser.add_argument(
        "--short",
        action="store_true",
        help="Show short quick reference only",
    )
    args = parser.parse_args()

    if args.short:
        print("\n\033[34mBookBrain Migration Quick Reference\033[0m\n")
        print("  ./scripts/migrate.sh status           # Check services")
        print("  ./scripts/migrate.sh dump             # Dump PostgreSQL")
        print("  ./scripts/migrate.sh restore --target # Restore PostgreSQL")
        print("  ./scripts/migrate.sh snapshot         # Create Qdrant snapshot")
        print("  ./scripts/migrate.sh sync-s3          # Sync to S3")
        print("  ./scripts/migrate.sh guide            # Full guide")
        print()
        return 0

    return print_guide()


if __name__ == "__main__":
    sys.exit(main())
