#!/usr/bin/env python3
"""Qdrant migration: snapshot creation and download."""

import argparse
import sys
from pathlib import Path

import httpx

from bookbrain.core.config import settings


def create_snapshot() -> int:
    """Create a snapshot of the Qdrant collection.

    Returns:
        Exit code (0 for success)
    """
    collection = settings.qdrant_collection
    url = f"{settings.qdrant_url}/collections/{collection}/snapshots"

    print(f"\n\033[34mCreating snapshot for collection '{collection}'...\033[0m\n")

    try:
        response = httpx.post(url, timeout=60.0)

        if response.status_code == 200:
            data = response.json()
            result = data.get("result", {})
            snapshot_name = result.get("name", "unknown")
            snapshot_size = result.get("size", 0)

            print(f"\033[32m✓ Snapshot created: {snapshot_name}\033[0m")
            print(f"\033[32m✓ Size: {snapshot_size:,} bytes\033[0m")
            print(f"\nSnapshot path on Qdrant server:")
            print(f"  /qdrant/snapshots/{collection}/{snapshot_name}")
            print(f"\nTo download:")
            print(f"  ./scripts/migrate.sh snapshot --download ./backup/")
            return 0
        else:
            print(f"\033[31mError: Failed to create snapshot (HTTP {response.status_code})\033[0m")
            if response.text:
                print(response.text)
            return 1

    except httpx.ConnectError:
        print(f"\033[31mError: Cannot connect to Qdrant at {settings.qdrant_url}\033[0m")
        print("Check QDRANT_URL environment variable and ensure Qdrant is running.")
        return 1
    except Exception as e:
        print(f"\033[31mError: {e}\033[0m")
        return 1


def list_snapshots() -> list[dict]:
    """List available snapshots.

    Returns:
        List of snapshot info dicts
    """
    collection = settings.qdrant_collection
    url = f"{settings.qdrant_url}/collections/{collection}/snapshots"

    try:
        response = httpx.get(url, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            return data.get("result", [])
        return []
    except Exception:
        return []


def download_snapshot(output_dir: str, snapshot_name: str | None = None) -> int:
    """Download a snapshot from Qdrant.

    Args:
        output_dir: Directory to save the snapshot
        snapshot_name: Specific snapshot to download (latest if None)

    Returns:
        Exit code (0 for success)
    """
    collection = settings.qdrant_collection
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get list of snapshots
    snapshots = list_snapshots()
    if not snapshots:
        print("\033[31mError: No snapshots available\033[0m")
        print("Run 'migrate.sh snapshot' first to create a snapshot.")
        return 1

    # Use latest snapshot if not specified
    if snapshot_name is None:
        # Sort by creation time (name contains timestamp)
        snapshots.sort(key=lambda x: x.get("name", ""), reverse=True)
        snapshot_name = snapshots[0].get("name")

    print(f"\n\033[34mDownloading snapshot '{snapshot_name}'...\033[0m\n")

    # Download the snapshot
    url = f"{settings.qdrant_url}/collections/{collection}/snapshots/{snapshot_name}"

    try:
        with httpx.stream("GET", url, timeout=300.0) as response:
            if response.status_code != 200:
                print(f"\033[31mError: Failed to download (HTTP {response.status_code})\033[0m")
                return 1

            output_file = output_path / snapshot_name
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(output_file, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = (downloaded / total_size) * 100
                        print(f"\r  Progress: {pct:.1f}% ({downloaded:,}/{total_size:,} bytes)", end="")

            print()  # New line after progress
            print(f"\033[32m✓ Downloaded to: {output_file}\033[0m")
            print(f"\033[32m✓ Size: {output_file.stat().st_size:,} bytes\033[0m")

            print(f"\nTo restore on target Qdrant:")
            print(f"  1. Copy {output_file} to target server")
            print(f"  2. Use Qdrant API to recover from snapshot:")
            print(f"     PUT /collections/{collection}/snapshots/recover")
            print(f"     Body: {{\"location\": \"/path/to/{snapshot_name}\"}}")

            return 0

    except httpx.ConnectError:
        print(f"\033[31mError: Cannot connect to Qdrant at {settings.qdrant_url}\033[0m")
        return 1
    except Exception as e:
        print(f"\033[31mError: {e}\033[0m")
        return 1


def show_snapshots() -> int:
    """Show list of available snapshots.

    Returns:
        Exit code (0 for success)
    """
    collection = settings.qdrant_collection
    print(f"\n\033[34mSnapshots for collection '{collection}':\033[0m\n")

    snapshots = list_snapshots()
    if not snapshots:
        print("  No snapshots available")
        print("\n  Create one with: ./scripts/migrate.sh snapshot")
        return 0

    for snap in sorted(snapshots, key=lambda x: x.get("name", ""), reverse=True):
        name = snap.get("name", "unknown")
        size = snap.get("size", 0)
        print(f"  • {name} ({size:,} bytes)")

    print()
    return 0


def delete_snapshot(snapshot_name: str) -> bool:
    """Delete a specific snapshot from Qdrant server.

    Args:
        snapshot_name: Name of the snapshot to delete

    Returns:
        True if deleted successfully, False otherwise
    """
    collection = settings.qdrant_collection
    url = f"{settings.qdrant_url}/collections/{collection}/snapshots/{snapshot_name}"

    try:
        response = httpx.delete(url, timeout=30.0)
        return response.status_code == 200
    except Exception:
        return False


def cleanup_snapshots(keep_count: int = 3) -> int:
    """Clean up old snapshots, keeping only the most recent ones.

    Args:
        keep_count: Number of recent snapshots to keep

    Returns:
        Exit code (0 for success)
    """
    collection = settings.qdrant_collection
    print(f"\n\033[34mCleaning up old snapshots for collection '{collection}'...\033[0m\n")

    snapshots = list_snapshots()
    if not snapshots:
        print("  No snapshots to clean up")
        return 0

    # Sort by name (contains timestamp) descending
    sorted_snapshots = sorted(snapshots, key=lambda x: x.get("name", ""), reverse=True)

    # Keep the most recent ones
    to_delete = sorted_snapshots[keep_count:]

    if not to_delete:
        print(f"  No cleanup needed (only {len(snapshots)} snapshot(s) exist)")
        return 0

    print(f"  Keeping {keep_count} most recent snapshots")
    print(f"  Deleting {len(to_delete)} old snapshot(s)...")

    deleted_count = 0
    for snap in to_delete:
        name = snap.get("name", "unknown")
        if delete_snapshot(name):
            print(f"    \033[32m✓ Deleted: {name}\033[0m")
            deleted_count += 1
        else:
            print(f"    \033[31m✗ Failed to delete: {name}\033[0m")

    print(f"\n\033[32m✓ Cleaned up {deleted_count} snapshot(s)\033[0m")
    return 0


def main() -> int:
    """Main entry point for Qdrant migration."""
    parser = argparse.ArgumentParser(description="Qdrant snapshot tool")
    parser.add_argument(
        "--download",
        metavar="DIR",
        help="Download latest snapshot to directory",
    )
    parser.add_argument(
        "--snapshot-name",
        help="Specific snapshot name to download",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available snapshots",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old snapshots (keeps 3 most recent)",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=3,
        help="Number of snapshots to keep when cleaning up (default: 3)",
    )

    args = parser.parse_args()

    if args.list:
        return show_snapshots()
    elif args.download:
        return download_snapshot(args.download, args.snapshot_name)
    elif args.cleanup:
        return cleanup_snapshots(keep_count=args.keep)
    else:
        return create_snapshot()


if __name__ == "__main__":
    sys.exit(main())
