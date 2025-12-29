"""Tests for migration scripts."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestMigrateStatus:
    """Tests for migrate_status module."""

    def test_check_postgresql_success(self):
        """Test PostgreSQL check with successful connection."""
        import psycopg

        from bookbrain.scripts.migrate_status import check_postgresql

        with patch.object(psycopg, "connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_cur.fetchone.return_value = (5,)
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=False)
            mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
            mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
            mock_connect.return_value = mock_conn

            ok, msg = check_postgresql()

            assert ok is True
            assert "5 books" in msg

    def test_check_postgresql_connection_error(self):
        """Test PostgreSQL check with connection error."""
        import psycopg

        from bookbrain.scripts.migrate_status import check_postgresql

        with patch.object(psycopg, "connect") as mock_connect:
            mock_connect.side_effect = Exception("Connection refused")

            ok, msg = check_postgresql()

            assert ok is False
            assert "Connection refused" in msg

    def test_check_qdrant_success(self):
        """Test Qdrant check with successful connection."""
        from bookbrain.scripts.migrate_status import check_qdrant

        with patch("bookbrain.scripts.migrate_status.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": {"points_count": 100}}
            mock_httpx.get.return_value = mock_response

            ok, msg = check_qdrant()

            assert ok is True
            assert "100 points" in msg

    def test_check_qdrant_connection_error(self):
        """Test Qdrant check with connection error."""
        import httpx

        from bookbrain.scripts.migrate_status import check_qdrant

        with patch("bookbrain.scripts.migrate_status.httpx") as mock_httpx:
            mock_httpx.ConnectError = httpx.ConnectError
            mock_httpx.get.side_effect = httpx.ConnectError("Connection refused")

            ok, msg = check_qdrant()

            assert ok is False
            assert "refused" in msg.lower()

    def test_check_s3_disabled(self):
        """Test S3 check when S3 is disabled."""
        from bookbrain.scripts.migrate_status import check_s3

        with patch("bookbrain.scripts.migrate_status.settings") as mock_settings:
            mock_settings.s3_enabled = False

            ok, msg = check_s3()

            assert ok is True
            assert "Disabled" in msg


class TestMigratePg:
    """Tests for migrate_pg module."""

    def test_parse_database_url(self):
        """Test database URL parsing."""
        from bookbrain.scripts.migrate_pg import parse_database_url

        result = parse_database_url("postgresql://user:pass@host:5432/dbname")

        assert result["host"] == "host"
        assert result["port"] == 5432
        assert result["user"] == "user"
        assert result["password"] == "pass"
        assert result["database"] == "dbname"

    def test_parse_database_url_defaults(self):
        """Test database URL parsing with defaults."""
        from bookbrain.scripts.migrate_pg import parse_database_url

        result = parse_database_url("postgresql://localhost/mydb")

        assert result["host"] == "localhost"
        assert result["port"] == 5432
        assert result["user"] is None or result["user"] == "postgres"
        assert result["database"] == "mydb"

    def test_check_pg_tools_available(self):
        """Test pg tools availability check."""
        from bookbrain.scripts.migrate_pg import check_pg_tools

        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: f"/usr/bin/{x}"

            result = check_pg_tools()

            assert result is True

    def test_check_pg_tools_missing(self):
        """Test pg tools check when tools are missing."""
        from bookbrain.scripts.migrate_pg import check_pg_tools

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None

            result = check_pg_tools()

            assert result is False

    def test_dump_database_success(self, tmp_path):
        """Test successful database dump."""
        from bookbrain.scripts.migrate_pg import dump_database

        output_file = tmp_path / "test_dump.sql"

        with (
            patch("bookbrain.scripts.migrate_pg.check_pg_tools", return_value=True),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stderr="")

            # Create a dummy file to simulate pg_dump output
            output_file.write_bytes(b"dummy dump content")

            result = dump_database(str(output_file))

            assert result == 0
            mock_run.assert_called()


class TestMigrateQdrant:
    """Tests for migrate_qdrant module."""

    def test_create_snapshot_success(self):
        """Test successful snapshot creation."""
        from bookbrain.scripts.migrate_qdrant import create_snapshot

        with patch("bookbrain.scripts.migrate_qdrant.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": {"name": "chunks-2024-01-01.snapshot", "size": 1000000}
            }
            mock_httpx.post.return_value = mock_response

            result = create_snapshot()

            assert result == 0

    def test_create_snapshot_connection_error(self):
        """Test snapshot creation with connection error."""
        import httpx

        from bookbrain.scripts.migrate_qdrant import create_snapshot

        with patch("bookbrain.scripts.migrate_qdrant.httpx") as mock_httpx:
            mock_httpx.ConnectError = httpx.ConnectError
            mock_httpx.post.side_effect = httpx.ConnectError("Connection refused")

            result = create_snapshot()

            assert result == 1

    def test_list_snapshots(self):
        """Test listing snapshots."""
        from bookbrain.scripts.migrate_qdrant import list_snapshots

        with patch("bookbrain.scripts.migrate_qdrant.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": [
                    {"name": "snap1.snapshot", "size": 1000},
                    {"name": "snap2.snapshot", "size": 2000},
                ]
            }
            mock_httpx.get.return_value = mock_response

            result = list_snapshots()

            assert len(result) == 2


class TestMigrateS3:
    """Tests for migrate_s3 module."""

    def test_list_local_files(self, tmp_path):
        """Test listing local files."""
        from bookbrain.scripts.migrate_s3 import list_local_files

        # Create test files
        (tmp_path / "test1.pdf").write_bytes(b"pdf1")
        (tmp_path / "test2.pdf").write_bytes(b"pdf2")
        (tmp_path / "test.txt").write_bytes(b"txt")

        result = list_local_files(tmp_path, "*.pdf")

        assert len(result) == 2
        assert all(f.suffix == ".pdf" for f in result)

    def test_list_local_files_empty_dir(self, tmp_path):
        """Test listing files in empty directory."""
        from bookbrain.scripts.migrate_s3 import list_local_files

        result = list_local_files(tmp_path, "*.pdf")

        assert len(result) == 0

    def test_list_local_files_nonexistent_dir(self):
        """Test listing files in non-existent directory."""
        from bookbrain.scripts.migrate_s3 import list_local_files

        result = list_local_files(Path("/nonexistent"), "*.pdf")

        assert len(result) == 0


class TestMigrateGuide:
    """Tests for migrate_guide module."""

    def test_print_guide(self, capsys):
        """Test guide output."""
        from bookbrain.scripts.migrate_guide import print_guide

        result = print_guide()

        captured = capsys.readouterr()
        assert result == 0
        assert "BookBrain Migration Guide" in captured.out
        assert "PostgreSQL" in captured.out
        assert "Qdrant" in captured.out
        assert "S3" in captured.out


class TestMigrateShellScript:
    """Tests for migrate.sh shell script."""

    def test_script_exists(self):
        """Test that migrate.sh exists and is executable."""
        script_path = Path(__file__).parent.parent / "scripts" / "migrate.sh"
        assert script_path.exists()
        assert script_path.stat().st_mode & 0o111  # Check executable bit

    def test_script_help(self):
        """Test migrate.sh help output."""
        script_path = Path(__file__).parent.parent / "scripts" / "migrate.sh"

        result = subprocess.run(
            [str(script_path), "help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "BookBrain Data Migration Tool" in result.stdout
        assert "status" in result.stdout
        assert "dump" in result.stdout
        assert "restore" in result.stdout
        assert "snapshot" in result.stdout
        assert "sync-s3" in result.stdout
        assert "guide" in result.stdout

    def test_script_unknown_command(self):
        """Test migrate.sh with unknown command."""
        script_path = Path(__file__).parent.parent / "scripts" / "migrate.sh"

        result = subprocess.run(
            [str(script_path), "unknown"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Error" in result.stderr or "Unknown command" in result.stdout
