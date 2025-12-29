#!/usr/bin/env python3
"""PostgreSQL migration: dump and restore."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from bookbrain.core.config import settings


def parse_database_url(url: str) -> dict:
    """Parse database URL into components."""
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "database": parsed.path.lstrip("/") or "postgres",
    }


def check_pg_tools() -> bool:
    """Check if pg_dump and pg_restore are available."""
    pg_dump = shutil.which("pg_dump")
    pg_restore = shutil.which("pg_restore")

    if not pg_dump:
        print("\033[31mError: pg_dump not found\033[0m")
        print("Install PostgreSQL client tools:")
        print("  macOS: brew install postgresql")
        print("  Ubuntu: sudo apt install postgresql-client")
        return False

    if not pg_restore:
        print("\033[31mError: pg_restore not found\033[0m")
        return False

    return True


def dump_database(output_file: str, full_schema: bool = False) -> int:
    """Dump PostgreSQL database to a file.

    Args:
        output_file: Path to output dump file
        full_schema: If True, dump entire database; if False, only books table with sequences

    Returns:
        Exit code (0 for success)
    """
    if not check_pg_tools():
        return 1

    db = parse_database_url(settings.database_url)
    output_path = Path(output_file)

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n\033[34mDumping database to {output_file}...\033[0m\n")

    # Set password in environment
    env = os.environ.copy()
    if db["password"]:
        env["PGPASSWORD"] = db["password"]

    cmd = [
        "pg_dump",
        "--format=custom",
        f"--file={output_file}",
        f"--host={db['host']}",
        f"--port={db['port']}",
        f"--username={db['user']}",
    ]

    if full_schema:
        # Dump entire database schema and data
        print("\033[32mDumping full database schema and data...\033[0m")
        cmd.append("--schema=public")  # Include all public schema objects
    else:
        # Dump books table (includes owned sequences like books_id_seq automatically)
        cmd.append("--table=books")
        print("\033[32mDumping books table (includes owned sequences and constraints)...\033[0m")

    cmd.append(db["database"])

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"\033[31mError: pg_dump failed\033[0m")
            if result.stderr:
                print(result.stderr)
            return 1

        file_size = output_path.stat().st_size
        print(f"\033[32m✓ Dump complete: {output_file} ({file_size:,} bytes)\033[0m")

        # Verify dump content
        verify_cmd = ["pg_restore", "--list", output_file]
        verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
        if verify_result.returncode == 0:
            lines = [
                l for l in verify_result.stdout.split("\n") if l and not l.startswith(";")
            ]
            print(f"\033[32m✓ Dump contains {len(lines)} objects\033[0m")

        return 0
    except FileNotFoundError:
        print("\033[31mError: pg_dump not found in PATH\033[0m")
        return 1
    except Exception as e:
        print(f"\033[31mError: {e}\033[0m")
        return 1


def restore_database(dump_file: str, target_url: str | None = None) -> int:
    """Restore PostgreSQL dump to target database.

    Args:
        dump_file: Path to dump file
        target_url: Target database URL (if None, uses TARGET_DATABASE_URL env var)

    Returns:
        Exit code (0 for success)
    """
    if not check_pg_tools():
        return 1

    dump_path = Path(dump_file)
    if not dump_path.exists():
        print(f"\033[31mError: Dump file not found: {dump_file}\033[0m")
        print("Run 'migrate.sh dump' first to create a dump file.")
        return 1

    # Use environment variable if target_url not provided (security best practice)
    if target_url is None:
        target_url = os.environ.get("TARGET_DATABASE_URL")
        if not target_url:
            print("\033[31mError: Target database URL not specified\033[0m")
            print("\nProvide target URL via one of:")
            print("  1. Environment variable: export TARGET_DATABASE_URL=postgresql://...")
            print("  2. CLI argument: --target postgresql://... (not recommended for security)")
            return 1
        print("\033[32m✓ Using TARGET_DATABASE_URL from environment\033[0m")

    db = parse_database_url(target_url)

    print(f"\n\033[34mRestoring to {db['host']}:{db['port']}/{db['database']}...\033[0m\n")
    print("\033[33mWarning: This will overwrite existing data in the books table.\033[0m")
    print("\033[32mUsing --single-transaction for atomic restore (rollback on error)\033[0m")

    # Set password in environment
    env = os.environ.copy()
    if db["password"]:
        env["PGPASSWORD"] = db["password"]

    cmd = [
        "pg_restore",
        f"--host={db['host']}",
        f"--port={db['port']}",
        f"--username={db['user']}",
        f"--dbname={db['database']}",
        "--single-transaction",  # Atomic restore - rollback on any error
        "--clean",  # Clean (drop) objects before recreating
        "--if-exists",  # Don't error if objects don't exist
        "--no-owner",  # Don't set ownership
        "--no-privileges",  # Don't set privileges
        dump_file,
    ]

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        # pg_restore may return non-zero even on partial success
        if result.returncode != 0 and result.stderr:
            # Filter out common non-fatal errors
            errors = [
                l for l in result.stderr.split("\n")
                if l and "error" in l.lower() and "does not exist" not in l.lower()
            ]
            if errors:
                print(f"\033[31mRestore failed (transaction rolled back):\033[0m")
                for error in errors:
                    print(f"  {error}")
                return 1

        print(f"\033[32m✓ Restore complete\033[0m")

        # Verify by counting records
        import psycopg

        with psycopg.connect(target_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM books")
                count = cur.fetchone()[0]
                print(f"\033[32m✓ Verified: {count} books in target database\033[0m")

        return 0
    except FileNotFoundError:
        print("\033[31mError: pg_restore not found in PATH\033[0m")
        return 1
    except Exception as e:
        print(f"\033[31mError: {e}\033[0m")
        return 1


def main() -> int:
    """Main entry point for PostgreSQL migration."""
    parser = argparse.ArgumentParser(description="PostgreSQL migration tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Dump command
    dump_parser = subparsers.add_parser("dump", help="Dump database")
    dump_parser.add_argument(
        "--output",
        default="bookbrain_dump.sql",
        help="Output file path (default: bookbrain_dump.sql)",
    )
    dump_parser.add_argument(
        "--full",
        action="store_true",
        help="Dump entire database schema (default: books table only)",
    )

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore database")
    restore_parser.add_argument(
        "--target",
        required=False,
        default=None,
        help="Target database URL (or use TARGET_DATABASE_URL env var, recommended)",
    )
    restore_parser.add_argument(
        "--dump-file",
        default="bookbrain_dump.sql",
        help="Dump file to restore (default: bookbrain_dump.sql)",
    )

    args = parser.parse_args()

    if args.command == "dump":
        return dump_database(args.output, full_schema=args.full)
    elif args.command == "restore":
        return restore_database(args.dump_file, args.target)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
