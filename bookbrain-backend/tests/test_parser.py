"""Tests for PDF parsing service."""

import pytest
import respx
from httpx import Response

from bookbrain.core.exceptions import PDFReadError, StormParseAPIError
from bookbrain.models.parser import ParsedDocument
from bookbrain.services.parser import parse_pdf


class TestParsePdf:
    """Tests for parse_pdf function."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_parse_pdf_success(self, tmp_path, mock_settings):
        """Test successful PDF parsing."""
        # Create a temporary PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        # Mock the submit request
        submit_route = respx.post(
            f"{mock_settings.storm_parse_api_base_url}/parse/by-file"
        ).mock(
            return_value=Response(
                200,
                json={
                    "jobId": "test-job-123",
                    "state": "REQUESTED",
                    "requestedAt": "2024-01-01T00:00:00Z",
                },
            )
        )

        # Mock the poll request - return COMPLETED immediately
        poll_route = respx.get(
            f"{mock_settings.storm_parse_api_base_url}/parse/job/test-job-123"
        ).mock(
            return_value=Response(
                200,
                json={
                    "jobId": "test-job-123",
                    "state": "COMPLETED",
                    "requestedAt": "2024-01-01T00:00:00Z",
                    "completedAt": "2024-01-01T00:00:05Z",
                    "pages": [
                        {
                            "pageNumber": 1,
                            "content": "Page 1 content",
                            "tables": [{"id": "table1", "data": "..."}],
                            "figures": [],
                        },
                        {
                            "pageNumber": 2,
                            "content": "Page 2 content",
                            "tables": [],
                            "figures": [{"id": "fig1", "caption": "..."}],
                        },
                    ],
                },
            )
        )

        result = await parse_pdf(str(pdf_file))

        assert isinstance(result, ParsedDocument)
        assert result.total_pages == 2
        assert len(result.pages) == 2
        assert result.pages[0].page_number == 1
        assert result.pages[0].content == "Page 1 content"
        assert len(result.pages[0].tables) == 1
        assert result.pages[0].tables[0]["id"] == "table1"
        assert result.pages[1].page_number == 2
        assert result.pages[1].content == "Page 2 content"
        assert len(result.pages[1].figures) == 1
        assert result.pages[1].figures[0]["id"] == "fig1"
        assert submit_route.called
        assert poll_route.called

    @pytest.mark.asyncio
    async def test_parse_pdf_file_not_found(self):
        """Test error when PDF file does not exist."""
        with pytest.raises(PDFReadError) as exc_info:
            await parse_pdf("/nonexistent/path/file.pdf")

        assert "/nonexistent/path/file.pdf" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parse_pdf_not_a_file(self, tmp_path):
        """Test error when path is a directory, not a file."""
        with pytest.raises(PDFReadError):
            await parse_pdf(str(tmp_path))

    @pytest.mark.asyncio
    @respx.mock
    async def test_parse_pdf_api_error(self, tmp_path, mock_settings):
        """Test error when Storm Parse API returns error."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        # Mock API returning 400 error
        respx.post(f"{mock_settings.storm_parse_api_base_url}/parse/by-file").mock(
            return_value=Response(400, json={"error": "Bad request"})
        )

        with pytest.raises(StormParseAPIError) as exc_info:
            await parse_pdf(str(pdf_file))

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @respx.mock
    async def test_parse_pdf_api_timeout_with_retry(self, tmp_path, mock_settings):
        """Test timeout with retry logic."""
        import httpx

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        # Mock: first call times out, second succeeds
        call_count = 0

        def side_effect(request):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.TimeoutException("Connection timeout")
            return Response(
                200,
                json={
                    "jobId": "test-job-456",
                    "state": "REQUESTED",
                    "requestedAt": "2024-01-01T00:00:00Z",
                },
            )

        respx.post(f"{mock_settings.storm_parse_api_base_url}/parse/by-file").mock(
            side_effect=side_effect
        )

        # Mock poll returning COMPLETED
        respx.get(
            f"{mock_settings.storm_parse_api_base_url}/parse/job/test-job-456"
        ).mock(
            return_value=Response(
                200,
                json={
                    "jobId": "test-job-456",
                    "state": "COMPLETED",
                    "pages": [{"pageNumber": 1, "content": "Content"}],
                },
            )
        )

        result = await parse_pdf(str(pdf_file))

        assert result.total_pages == 1
        assert call_count == 2  # First timeout, then success

    @pytest.mark.asyncio
    @respx.mock
    async def test_parse_pdf_5xx_retry(self, tmp_path, mock_settings):
        """Test 5xx error triggers retry."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        call_count = 0

        def side_effect(request):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return Response(503, text="Service Unavailable")
            return Response(
                200,
                json={
                    "jobId": "test-job-789",
                    "state": "REQUESTED",
                    "requestedAt": "2024-01-01T00:00:00Z",
                },
            )

        respx.post(f"{mock_settings.storm_parse_api_base_url}/parse/by-file").mock(
            side_effect=side_effect
        )

        respx.get(
            f"{mock_settings.storm_parse_api_base_url}/parse/job/test-job-789"
        ).mock(
            return_value=Response(
                200,
                json={
                    "jobId": "test-job-789",
                    "state": "COMPLETED",
                    "pages": [{"pageNumber": 1, "content": "Retry success"}],
                },
            )
        )

        result = await parse_pdf(str(pdf_file))

        assert result.pages[0].content == "Retry success"
        assert call_count == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_parse_pdf_polling_multiple_states(self, tmp_path, mock_settings):
        """Test polling through multiple states before completion."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        respx.post(f"{mock_settings.storm_parse_api_base_url}/parse/by-file").mock(
            return_value=Response(
                200,
                json={"jobId": "poll-job", "state": "REQUESTED"},
            )
        )

        poll_count = 0
        states = ["REQUESTED", "ACCEPTED", "PROCESSED", "COMPLETED"]

        def poll_side_effect(request):
            nonlocal poll_count
            state = states[min(poll_count, len(states) - 1)]
            poll_count += 1

            response = {
                "jobId": "poll-job",
                "state": state,
            }
            if state == "COMPLETED":
                response["pages"] = [{"pageNumber": 1, "content": "Final content"}]

            return Response(200, json=response)

        respx.get(f"{mock_settings.storm_parse_api_base_url}/parse/job/poll-job").mock(
            side_effect=poll_side_effect
        )

        result = await parse_pdf(str(pdf_file))

        assert result.pages[0].content == "Final content"
        assert poll_count == 4  # REQUESTED -> ACCEPTED -> PROCESSED -> COMPLETED

    @pytest.mark.asyncio
    @respx.mock
    async def test_parse_pdf_job_failed(self, tmp_path, mock_settings):
        """Test error when job fails."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        respx.post(f"{mock_settings.storm_parse_api_base_url}/parse/by-file").mock(
            return_value=Response(
                200,
                json={"jobId": "fail-job", "state": "REQUESTED"},
            )
        )

        respx.get(f"{mock_settings.storm_parse_api_base_url}/parse/job/fail-job").mock(
            return_value=Response(
                200,
                json={"jobId": "fail-job", "state": "FAILED"},
            )
        )

        with pytest.raises(StormParseAPIError) as exc_info:
            await parse_pdf(str(pdf_file))

        assert "FAILED" in str(exc_info.value)

    @pytest.mark.asyncio
    @respx.mock
    async def test_parse_pdf_pages_sorted(self, tmp_path, mock_settings):
        """Test that pages are sorted by page number."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        respx.post(f"{mock_settings.storm_parse_api_base_url}/parse/by-file").mock(
            return_value=Response(
                200,
                json={"jobId": "sort-job", "state": "REQUESTED"},
            )
        )

        # Return pages out of order
        respx.get(f"{mock_settings.storm_parse_api_base_url}/parse/job/sort-job").mock(
            return_value=Response(
                200,
                json={
                    "jobId": "sort-job",
                    "state": "COMPLETED",
                    "pages": [
                        {"pageNumber": 3, "content": "Page 3"},
                        {"pageNumber": 1, "content": "Page 1"},
                        {"pageNumber": 2, "content": "Page 2"},
                    ],
                },
            )
        )

        result = await parse_pdf(str(pdf_file))

        assert result.pages[0].page_number == 1
        assert result.pages[1].page_number == 2
        assert result.pages[2].page_number == 3
