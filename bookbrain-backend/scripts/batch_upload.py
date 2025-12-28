#!/usr/bin/env python
"""
Batch Upload CLI for BookBrain.

Upload multiple PDF files from a directory to BookBrain for indexing.

Usage:
    python -m scripts.batch_upload --source ~/books/
    python -m scripts.batch_upload --source ~/books/ --dry-run
    python -m scripts.batch_upload --source ~/books/ --parallel 3
    python -m scripts.batch_upload --source ~/books/ --author "Unknown" --failed-file ./failed.txt

Alternative (from bookbrain-backend directory):
    uv run python scripts/batch_upload.py --source ~/books/
"""

import argparse
import asyncio
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

# Add the src directory to the path for imports when run directly
# Note: Prefer running with `python -m scripts.batch_upload` to avoid this
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bookbrain.core.exceptions import (
    DuplicateBookError,
    IndexingError,
    InvalidFileFormatError,
    PDFReadError,
)
from bookbrain.services.batch_indexer import BatchIndexingResult, index_local_pdf

# Default concurrency limit for parallel processing
DEFAULT_CONCURRENCY = 3
MAX_CONCURRENCY = 10

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Suppress noisy loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


@dataclass
class BatchResult:
    """Result of batch processing."""

    total: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    success_list: list[tuple[str, int]] = field(default_factory=list)  # (filename, book_id)
    failed_list: list[tuple[str, str]] = field(default_factory=list)  # (filename, error)
    skipped_list: list[tuple[str, str]] = field(default_factory=list)  # (filename, reason)
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def elapsed_time(self) -> float:
        """Total elapsed time in seconds."""
        return self.end_time - self.start_time

    @property
    def elapsed_time_str(self) -> str:
        """Formatted elapsed time."""
        elapsed = self.elapsed_time
        if elapsed < 60:
            return f"{elapsed:.1f}s"
        elif elapsed < 3600:
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            return f"{minutes}m {seconds}s"
        else:
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            return f"{hours}h {minutes}m"


def scan_pdf_files(source_dir: Path) -> list[Path]:
    """
    Scan directory for PDF files.

    Args:
        source_dir: Directory to scan

    Returns:
        List of PDF file paths, sorted alphabetically
    """
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    if not source_dir.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {source_dir}")

    pdf_files = sorted(source_dir.glob("*.pdf"))

    if not pdf_files:
        logger.warning(f"No PDF files found in {source_dir}")

    return pdf_files


def print_progress(
    current: int,
    total: int,
    filename: str,
    status: str = "Processing",
) -> None:
    """Print progress indicator."""
    print(f"\n[{current}/{total}] {status}: {filename}")


def print_step(message: str, success: bool = True) -> None:
    """Print step completion."""
    symbol = "✓" if success else "✗"
    print(f"  {symbol} {message}")


def print_final_report(result: BatchResult) -> None:
    """Print final batch processing report."""
    print("\n" + "=" * 50)
    print("=== Batch Upload Complete ===")
    print("=" * 50)
    print(f"Total files: {result.total}")
    print(f"  ✓ Success: {result.success}")
    print(f"  ✗ Failed: {result.failed}")
    print(f"  ○ Skipped (duplicate): {result.skipped}")
    print()
    print(f"Total time: {result.elapsed_time_str}")
    if result.success > 0:
        avg_time = result.elapsed_time / result.success
        print(f"Average per file: {avg_time:.1f}s")
    print("=" * 50)


def save_failed_list(failed_list: list[tuple[str, str]], output_path: Path) -> None:
    """Save failed file list to a file."""
    with open(output_path, "w") as f:
        f.write("# Failed files during batch upload\n")
        f.write(f"# Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for filename, error in failed_list:
            f.write(f"{filename}\n")
            f.write(f"  Error: {error}\n\n")
    print(f"\nFailed files saved to: {output_path}")


class ProcessingTask(NamedTuple):
    """Represents a file processing task with its result."""

    pdf_path: Path
    index: int
    result: BatchIndexingResult | None
    error: str | None


async def process_single_file(
    pdf_path: Path,
    current: int,
    total: int,
    author: str | None = None,
    skip_existing: bool = True,
    quiet: bool = False,
) -> BatchIndexingResult | None:
    """
    Process a single PDF file.

    Args:
        pdf_path: Path to the PDF file
        current: Current file number (1-indexed)
        total: Total number of files
        author: Default author for books
        skip_existing: Skip files with existing titles
        quiet: If True, suppress progress output (for parallel mode)

    Returns:
        BatchIndexingResult on success, None on failure
    """
    filename = pdf_path.name
    if not quiet:
        print_progress(current, total, filename)

    start_time = time.time()

    try:
        result = await index_local_pdf(
            file_path=pdf_path,
            author=author,
            skip_existing=skip_existing,
        )

        if result.skipped:
            if not quiet:
                print_step(f"Skipped: {result.skip_reason}", success=True)
            return result

        elapsed = time.time() - start_time
        if not quiet:
            print_step(f"Parsed ({elapsed:.1f}s)")
            print_step(f"Stored to {'S3' if result.file_path and result.file_path.startswith('s3://') else 'local'}")
            print_step(f"Chunked & Indexed: {result.chunks_count} chunks")
            print_step(f"Complete (book_id: {result.book_id})")

        return result

    except (InvalidFileFormatError, PDFReadError) as e:
        if not quiet:
            print_step(f"Failed: {e}", success=False)
            print("  → Skipping and continuing...")
        return None

    except DuplicateBookError as e:
        # When skip_existing=True but race condition occurred,
        # treat as skip rather than error
        if skip_existing:
            if not quiet:
                print_step(f"Skipped (race condition): {e}", success=True)
            return BatchIndexingResult(
                title=pdf_path.stem,
                status="skipped",
                skipped=True,
                skip_reason=f"Duplicate detected during creation: {e}",
            )
        if not quiet:
            print_step(f"Duplicate: {e}", success=False)
            print("  → Skipping and continuing...")
        return None

    except IndexingError as e:
        if not quiet:
            print_step(f"Indexing failed: {e}", success=False)
            print("  → Skipping and continuing...")
        return None

    except Exception as e:
        if not quiet:
            print_step(f"Unexpected error: {e}", success=False)
        logger.exception(f"Error processing {filename}")
        if not quiet:
            print("  → Skipping and continuing...")
        return None


async def process_file_with_semaphore(
    semaphore: asyncio.Semaphore,
    pdf_path: Path,
    index: int,
    total: int,
    author: str | None,
    skip_existing: bool,
) -> ProcessingTask:
    """Process a single file with semaphore for concurrency control."""
    async with semaphore:
        try:
            result = await index_local_pdf(
                file_path=pdf_path,
                author=author,
                skip_existing=skip_existing,
            )
            return ProcessingTask(pdf_path, index, result, None)
        except DuplicateBookError as e:
            # Handle race condition: treat as skip when skip_existing=True
            if skip_existing:
                return ProcessingTask(
                    pdf_path,
                    index,
                    BatchIndexingResult(
                        title=pdf_path.stem,
                        status="skipped",
                        skipped=True,
                        skip_reason=f"Duplicate detected: {e}",
                    ),
                    None,
                )
            return ProcessingTask(pdf_path, index, None, str(e))
        except (InvalidFileFormatError, PDFReadError, IndexingError) as e:
            return ProcessingTask(pdf_path, index, None, str(e))
        except Exception as e:
            logger.exception(f"Error processing {pdf_path.name}")
            return ProcessingTask(pdf_path, index, None, str(e))


async def run_batch_upload(
    source_dir: Path,
    author: str | None = None,
    skip_existing: bool = True,
    dry_run: bool = False,
    failed_file: Path | None = None,
    parallel: int = 1,
) -> BatchResult:
    """
    Run batch upload for all PDF files in a directory.

    Args:
        source_dir: Directory containing PDF files
        author: Default author for all books
        skip_existing: Skip files with existing titles
        dry_run: If True, only scan and list files without processing
        failed_file: Path to save failed files list (optional)
        parallel: Number of concurrent uploads (1 = sequential)

    Returns:
        BatchResult with processing statistics
    """
    result = BatchResult()
    result.start_time = time.time()

    # Scan for PDF files
    print(f"\nScanning directory: {source_dir}")
    pdf_files = scan_pdf_files(source_dir)
    result.total = len(pdf_files)

    if result.total == 0:
        print("No PDF files found. Exiting.")
        result.end_time = time.time()
        return result

    print(f"Found {result.total} PDF files")

    if dry_run:
        print("\n[DRY RUN] Files that would be processed:")
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"  [{i}/{result.total}] {pdf_path.name}")
        result.end_time = time.time()
        return result

    # Process files
    if parallel > 1:
        print(f"\nStarting parallel batch upload (concurrency={parallel}, skip_existing={skip_existing})...")
        result = await _run_parallel_upload(
            pdf_files, result, author, skip_existing, parallel
        )
    else:
        print(f"\nStarting sequential batch upload (skip_existing={skip_existing})...")
        result = await _run_sequential_upload(
            pdf_files, result, author, skip_existing
        )

    result.end_time = time.time()

    # Print final report
    print_final_report(result)

    # Save failed list
    if result.failed_list:
        output_path = failed_file or Path("failed.txt")
        save_failed_list(result.failed_list, output_path)

    return result


async def _run_sequential_upload(
    pdf_files: list[Path],
    result: BatchResult,
    author: str | None,
    skip_existing: bool,
) -> BatchResult:
    """Run uploads sequentially (original behavior)."""
    for i, pdf_path in enumerate(pdf_files, 1):
        try:
            indexing_result = await process_single_file(
                pdf_path=pdf_path,
                current=i,
                total=result.total,
                author=author,
                skip_existing=skip_existing,
            )

            if indexing_result is None:
                result.failed += 1
                result.failed_list.append((pdf_path.name, "Processing failed"))
            elif indexing_result.skipped:
                result.skipped += 1
                result.skipped_list.append((pdf_path.name, indexing_result.skip_reason or "Unknown"))
            else:
                result.success += 1
                result.success_list.append((pdf_path.name, indexing_result.book_id))

        except Exception as e:
            logger.exception(f"Unexpected error processing {pdf_path.name}")
            result.failed += 1
            result.failed_list.append((pdf_path.name, str(e)))

    return result


async def _run_parallel_upload(
    pdf_files: list[Path],
    result: BatchResult,
    author: str | None,
    skip_existing: bool,
    concurrency: int,
) -> BatchResult:
    """Run uploads in parallel with limited concurrency."""
    semaphore = asyncio.Semaphore(concurrency)
    total = result.total

    # Create all tasks
    tasks = [
        process_file_with_semaphore(
            semaphore, pdf_path, i, total, author, skip_existing
        )
        for i, pdf_path in enumerate(pdf_files, 1)
    ]

    # Process with progress reporting
    completed = 0
    for coro in asyncio.as_completed(tasks):
        task_result: ProcessingTask = await coro
        completed += 1

        # Print progress
        filename = task_result.pdf_path.name
        if task_result.error:
            print(f"[{completed}/{total}] ✗ {filename}: {task_result.error}")
            result.failed += 1
            result.failed_list.append((filename, task_result.error))
        elif task_result.result and task_result.result.skipped:
            print(f"[{completed}/{total}] ○ {filename}: Skipped")
            result.skipped += 1
            result.skipped_list.append((filename, task_result.result.skip_reason or "Unknown"))
        elif task_result.result:
            print(f"[{completed}/{total}] ✓ {filename}: book_id={task_result.result.book_id}, chunks={task_result.result.chunks_count}")
            result.success += 1
            result.success_list.append((filename, task_result.result.book_id))
        else:
            print(f"[{completed}/{total}] ✗ {filename}: Unknown error")
            result.failed += 1
            result.failed_list.append((filename, "Unknown error"))

    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch upload PDF files to BookBrain for indexing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python scripts/batch_upload.py --source ~/books/
  python scripts/batch_upload.py --source ~/books/ --dry-run
  python scripts/batch_upload.py --source ~/books/ --parallel 3
  python scripts/batch_upload.py --source ~/books/ --author "Unknown"
  python scripts/batch_upload.py --source ~/books/ --failed-file ./errors.txt

Performance:
  - Sequential mode (default): Processes files one by one
  - Parallel mode (--parallel N): Processes up to N files concurrently
  - Recommended: --parallel 3 for balanced performance
  - Max concurrency: {MAX_CONCURRENCY}
        """,
    )

    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Directory containing PDF files to upload",
    )

    parser.add_argument(
        "--author",
        type=str,
        default=None,
        help="Default author for all books (optional)",
    )

    parser.add_argument(
        "--failed-file",
        type=Path,
        default=None,
        help="File path to save failed files list (default: ./failed.txt)",
    )

    parser.add_argument(
        "--parallel",
        "-p",
        type=int,
        default=1,
        metavar="N",
        help=f"Number of concurrent uploads (1=sequential, max={MAX_CONCURRENCY})",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and list files without actually processing",
    )

    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Do not skip files with existing titles (may cause duplicates)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Validate parallel argument
    if args.parallel < 1:
        parser.error("--parallel must be at least 1")
    if args.parallel > MAX_CONCURRENCY:
        print(f"Warning: Limiting concurrency to {MAX_CONCURRENCY} (requested: {args.parallel})")
        args.parallel = MAX_CONCURRENCY

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("bookbrain").setLevel(logging.DEBUG)

    # Run batch upload
    try:
        result = asyncio.run(
            run_batch_upload(
                source_dir=args.source,
                author=args.author,
                skip_existing=not args.no_skip_existing,
                dry_run=args.dry_run,
                failed_file=args.failed_file,
                parallel=args.parallel,
            )
        )

        # Exit with error code if all files failed
        if result.total > 0 and result.success == 0 and not args.dry_run:
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except NotADirectoryError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nBatch upload interrupted by user.")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
