"""PDF parsing service using Storm Parse API."""

import asyncio
import logging
from pathlib import Path

import httpx

from bookbrain.core.config import settings
from bookbrain.core.exceptions import PDFReadError, StormParseAPIError
from bookbrain.models.parser import ParsedDocument, ParsedPage

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 1
RETRY_DELAY_SECONDS = 1.0

# Job states
STATE_COMPLETED = "COMPLETED"
TERMINAL_STATES = {"COMPLETED", "FAILED", "ERROR"}


async def parse_pdf(file_path: str, language: str = "ko") -> ParsedDocument:
    """
    Parse a PDF file using Storm Parse API.

    Args:
        file_path: Path to the PDF file to parse.
        language: Parsing language (default: "ko" for Korean).

    Returns:
        ParsedDocument containing extracted text and metadata.

    Raises:
        PDFReadError: If the PDF file cannot be read.
        StormParseAPIError: If the Storm Parse API call fails.
    """
    path = Path(file_path)

    if not path.exists():
        raise PDFReadError(file_path)

    if not path.is_file():
        raise PDFReadError(file_path)

    # Submit parse request and get jobId
    # We pass the Path object directly to handle file opening inside _submit_parse_request
    # to better support streaming and retries
    job_id = await _submit_parse_request(path, language)

    # Poll for result until completion
    return await _poll_for_result(job_id)


async def _submit_parse_request(
    file_path: Path,
    language: str,
    retry_count: int = 0,
) -> str:
    """
    Submit PDF file to Storm Parse API with streaming upload.

    Args:
        file_path: Path to the PDF file.
        language: Parsing language.
        retry_count: Current retry attempt (0-indexed).

    Returns:
        Job ID for polling the result.

    Raises:
        StormParseAPIError: If API call fails after retries.
        PDFReadError: If file cannot be read during upload.
    """
    url = f"{settings.storm_parse_api_base_url}/parse/by-file"

    try:
        async with httpx.AsyncClient(timeout=settings.storm_parse_timeout) as client:
            # Open file in binary mode for streaming upload
            with open(file_path, "rb") as f:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {settings.storm_parse_api_key}"},
                    files={"file": (file_path.name, f, "application/pdf")},
                    data={
                        "language": language,
                        "deleteOriginFile": "true",
                    },
                )

            if response.status_code >= 500 and retry_count < MAX_RETRIES:
                delay = RETRY_DELAY_SECONDS * (2**retry_count)
                logger.warning(
                    f"Storm Parse API returned {response.status_code}, "
                    f"retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                return await _submit_parse_request(
                    file_path, language, retry_count + 1
                )

            if response.status_code not in (200, 201):
                raise StormParseAPIError(
                    f"Storm Parse API error: {response.status_code} - {response.text}",
                    status_code=response.status_code,
                )

            data = response.json()
            job_id = data.get("jobId")
            if not job_id:
                raise StormParseAPIError("Storm Parse API did not return jobId")

            logger.info(f"Parse request submitted, jobId: {job_id}")
            return job_id

    except OSError as e:
        raise PDFReadError(str(file_path), cause=e)

    except httpx.TimeoutException as e:
        if retry_count < MAX_RETRIES:
            delay = RETRY_DELAY_SECONDS * (2**retry_count)
            logger.warning(
                f"Storm Parse API timeout, retrying in {delay}s..."
            )
            await asyncio.sleep(delay)
            return await _submit_parse_request(
                file_path, language, retry_count + 1
            )
        raise StormParseAPIError("Storm Parse API timeout", cause=e)

    except httpx.HTTPError as e:
        if retry_count < MAX_RETRIES:
            delay = RETRY_DELAY_SECONDS * (2**retry_count)
            logger.warning(
                f"Storm Parse API HTTP error, retrying in {delay}s..."
            )
            await asyncio.sleep(delay)
            return await _submit_parse_request(
                file_path, language, retry_count + 1
            )
        raise StormParseAPIError(f"Storm Parse API HTTP error: {e}", cause=e)


async def _poll_for_result(job_id: str) -> ParsedDocument:
    """
    Poll Storm Parse API for parsing result.

    Args:
        job_id: Job ID from the parse request.

    Returns:
        ParsedDocument when parsing is complete.

    Raises:
        StormParseAPIError: If polling fails or job fails.
    """
    url = f"{settings.storm_parse_api_base_url}/parse/job/{job_id}"
    poll_count = 0

    async with httpx.AsyncClient(timeout=settings.storm_parse_timeout) as client:
        while poll_count < settings.storm_parse_max_poll_attempts:
            try:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {settings.storm_parse_api_key}"},
                )

                if response.status_code != 200:
                    raise StormParseAPIError(
                        f"Storm Parse API poll error: {response.status_code}",
                        status_code=response.status_code,
                    )

                data = response.json()
                state = data.get("state", "")

                logger.debug(f"Job {job_id} state: {state}")

                if state == STATE_COMPLETED:
                    return _parse_job_response(data)

                if state in TERMINAL_STATES and state != STATE_COMPLETED:
                    raise StormParseAPIError(
                        f"Storm Parse job failed with state: {state}"
                    )

                # Not complete yet, wait and poll again
                poll_count += 1
                await asyncio.sleep(settings.storm_parse_poll_interval)

            except httpx.TimeoutException:
                logger.warning(f"Poll timeout for job {job_id}, retrying...")
                poll_count += 1
                await asyncio.sleep(settings.storm_parse_poll_interval)

            except httpx.HTTPError as e:
                raise StormParseAPIError(
                    f"Storm Parse API poll HTTP error: {e}", cause=e
                )

    max_wait = (
        settings.storm_parse_max_poll_attempts * settings.storm_parse_poll_interval
    )
    raise StormParseAPIError(
        f"Storm Parse job {job_id} did not complete within {max_wait}s"
    )


def _parse_job_response(response_data: dict) -> ParsedDocument:
    """
    Parse Storm Parse API job response into ParsedDocument.

    Args:
        response_data: JSON response from Storm Parse API job endpoint.

    Returns:
        ParsedDocument with extracted pages and metadata.

    Raises:
        StormParseAPIError: If response format is invalid.
    """
    try:
        pages_data = response_data.get("pages", [])
        pages = [
            ParsedPage(
                page_number=page.get("pageNumber", idx + 1),
                content=page.get("content", ""),
                tables=page.get("tables", []),
                figures=page.get("figures", []),
            )
            for idx, page in enumerate(pages_data)
        ]

        # Sort pages by page number
        pages.sort(key=lambda p: p.page_number)

        total_pages = len(pages)

        # Extract metadata if available
        metadata = {
            "jobId": response_data.get("jobId"),
            "requestedAt": response_data.get("requestedAt"),
            "completedAt": response_data.get("completedAt"),
            # Capture other potential metadata
            "title": response_data.get("title"),
            "author": response_data.get("author"),
        }

        # Filter out None values in metadata
        metadata = {k: v for k, v in metadata.items() if v is not None}

        return ParsedDocument(
            pages=pages,
            total_pages=total_pages,
            metadata=metadata,
        )
    except (KeyError, TypeError, ValueError) as e:
        raise StormParseAPIError(f"Invalid API response format: {e}", cause=e)