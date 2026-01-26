#!/bin/bash
# start.sh - Start the backend server with encrypted environment variables
#
# Usage:
#   ./start.sh              # Production mode (uses .env.vault)
#   ./start.sh --dev        # Dev mode (uses plaintext .env if available)
#
# For production deployment (Railway, etc.), set DOTENV_PRIVATE_KEY in the
# platform's environment variables, then run: dotenvx run -- uvicorn main:app

set -e

DEV_MODE=false

for arg in "$@"; do
    case $arg in
        --dev|-d)
            DEV_MODE=true
            ;;
    esac
done

if [ "$DEV_MODE" = true ]; then
    echo "Starting in DEV mode (plaintext .env)..."
    .venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000
else
    echo "Starting with dotenvx (encrypted .env.vault)..."
    dotenvx run -- .venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000
fi
