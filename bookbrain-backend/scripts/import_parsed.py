#!/usr/bin/env python3
"""
Import pre-parsed book to the system.
Skips Storm Parse API call, uploads PDF and parsed JSON to S3,
creates PostgreSQL record, and indexes to Qdrant.

Usage:
    cd bookbrain-backend
    uv run python scripts/import_parsed.py <pdf_path> <parsed_json_path>
"""

import asyncio
import json
import sys
import uuid
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bookbrain.core.config import settings
from bookbrain.services.storage import get_s3_client, save_parsed_result
from bookbrain.services.indexer import index_book
from bookbrain.services.sentence_chunker import chunk_text  # sentence-aware chunking
from bookbrain.models.parser import ParsedDocument, ParsedPage


async def import_parsed_book(pdf_path: str, parsed_json_path: str):
    """Import a pre-parsed PDF to the system."""

    pdf_file = Path(pdf_path)
    parsed_file = Path(parsed_json_path)

    if not pdf_file.exists():
        print(f"PDF file not found: {pdf_path}")
        return None

    if not parsed_file.exists():
        print(f"Parsed JSON file not found: {parsed_json_path}")
        return None

    # Load parsed result
    with open(parsed_file, "r", encoding="utf-8") as f:
        parsed_result = json.load(f)

    # Generate new IDs
    pdf_key = f"pdfs/{uuid.uuid4()}.pdf"

    # Extract title from first page or filename
    pages = parsed_result.get("pages", [])
    if pages and pages[0].get("content"):
        first_content = pages[0]["content"]
        lines = first_content.strip().split("\n")
        title = lines[0][:100] if lines else pdf_file.stem
    else:
        title = pdf_file.stem

    # Clean up title (remove markdown headers)
    if title.startswith("#"):
        title = title.lstrip("#").strip()

    print(f"Title: {title}")
    print(f"Pages: {len(pages)}")

    # 1. Upload PDF to S3
    print("\n1. Uploading PDF to S3...")
    s3_client = get_s3_client()
    with open(pdf_file, "rb") as f:
        s3_client.upload_fileobj(f, settings.s3_bucket_name, pdf_key)
    print(f"   Done: s3://{settings.s3_bucket_name}/{pdf_key}")

    # 2. Create book in PostgreSQL (direct connection to avoid pool issues in scripts)
    print("\n2. Creating book in PostgreSQL...")
    async with await psycopg.AsyncConnection.connect(
        settings.database_url, row_factory=dict_row
    ) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO books (title, author, file_path, total_pages, embedding_model)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (title, None, pdf_key, len(pages), None),
            )
            result = await cur.fetchone()
            await conn.commit()
            book_id = result["id"]
            print(f"   Done: book_id={book_id}")

    # 3. Save parsed result to S3 (sync function)
    print("\n3. Saving parsed result to S3...")
    parsed_key = save_parsed_result(book_id, parsed_result)
    print(f"   Done: {parsed_key}")

    # 4. Chunk text
    print("\n4. Chunking text...")
    parsed_pages = [
        ParsedPage(
            page_number=p["pageNumber"],
            content=p["content"],
        )
        for p in pages
    ]
    parsed_doc = ParsedDocument(
        pages=parsed_pages,
        total_pages=len(pages),
    )
    chunked_doc = chunk_text(parsed_doc)
    print(f"   Done: {chunked_doc.total_chunks} chunks")

    # 5. Index to Qdrant
    print("\n5. Indexing to Qdrant...")
    result = await index_book(book_id, chunked_doc)
    print(f"   Done: {result.chunks_stored} vectors stored")

    print(f"\n✅ Import complete! book_id={book_id}")
    return book_id


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python import_parsed.py <pdf_path> <parsed_json_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    parsed_json_path = sys.argv[2]

    book_id = asyncio.run(import_parsed_book(pdf_path, parsed_json_path))
