#!/bin/bash
# BookBrain Data Migration Tool
# Usage: ./scripts/migrate.sh <command> [options]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_usage() {
    echo "BookBrain Data Migration Tool"
    echo ""
    echo "Usage: ./scripts/migrate.sh <command> [options]"
    echo ""
    echo "Commands:"
    echo "  status                    Check connection status for all services"
    echo "  dump [--output FILE]      Dump PostgreSQL database to file"
    echo "  restore --target URL      Restore PostgreSQL dump to target database"
    echo "  snapshot [--download DIR] Create or download Qdrant snapshot"
    echo "  sync-s3 [--dry-run]       Sync local files to S3"
    echo "  guide                     Show migration guide"
    echo ""
    echo "Options:"
    echo "  --output FILE    Output file path for dump (default: bookbrain_dump.sql)"
    echo "  --target URL     Target database URL for restore"
    echo "  --download DIR   Download snapshot to directory"
    echo "  --dry-run        Show what would be synced without actually syncing"
    echo ""
    echo "Environment Variables:"
    echo "  DATABASE_URL     PostgreSQL connection URL"
    echo "  QDRANT_URL       Qdrant server URL (default: http://localhost:6333)"
    echo "  S3_ENABLED       Enable S3 storage (true/false)"
    echo "  S3_ENDPOINT_URL  S3-compatible endpoint URL"
    echo "  S3_ACCESS_KEY    S3 access key"
    echo "  S3_SECRET_KEY    S3 secret key"
    echo "  S3_BUCKET_NAME   S3 bucket name"
}

check_python() {
    if ! command -v python &> /dev/null; then
        echo -e "${RED}Error: Python is not installed${NC}"
        exit 1
    fi
}

run_python_module() {
    local module=$1
    shift
    cd "$BACKEND_DIR"

    # Check if running in virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        if [ -d ".venv" ]; then
            if [ -f ".venv/bin/activate" ]; then
                source .venv/bin/activate 2>/dev/null
                if [ -z "$VIRTUAL_ENV" ]; then
                    echo -e "${YELLOW}Warning: Failed to activate virtual environment${NC}"
                    echo -e "${YELLOW}You may need to install dependencies manually${NC}"
                fi
            else
                echo -e "${YELLOW}Warning: Virtual environment exists but activate script not found${NC}"
                echo -e "${YELLOW}Try: python -m venv .venv && source .venv/bin/activate${NC}"
            fi
        else
            echo -e "${YELLOW}Warning: No virtual environment found (.venv directory)${NC}"
            echo -e "${YELLOW}Using system Python. If you encounter import errors, create a venv:${NC}"
            echo -e "${YELLOW}  cd $BACKEND_DIR && python -m venv .venv && source .venv/bin/activate && pip install -e .${NC}"
        fi
    fi

    python -m bookbrain.scripts."$module" "$@"
}

case "${1:-}" in
    status)
        check_python
        run_python_module migrate_status "${@:2}"
        ;;
    dump)
        check_python
        run_python_module migrate_pg dump "${@:2}"
        ;;
    restore)
        check_python
        run_python_module migrate_pg restore "${@:2}"
        ;;
    snapshot)
        check_python
        run_python_module migrate_qdrant "${@:2}"
        ;;
    sync-s3)
        check_python
        run_python_module migrate_s3 "${@:2}"
        ;;
    guide)
        check_python
        run_python_module migrate_guide "${@:2}"
        ;;
    help|--help|-h)
        print_usage
        ;;
    *)
        echo -e "${RED}Error: Unknown command '${1:-}'${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac
