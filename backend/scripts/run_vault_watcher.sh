#!/bin/bash
# Wrapper script for vault watcher that loads .env variables
#
# NOTE: The vault watcher now starts automatically with the backend server
# when VAULT_WATCHER_USER_ID is configured. This script is for manual/standalone use.

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$BACKEND_DIR"

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
fi

# Run the watcher with initial sync using the virtual environment
exec "$BACKEND_DIR/.venv/bin/python" \
    -m scripts.vault_watcher \
    --user-id "${VAULT_WATCHER_USER_ID:-4d957e43-b34f-456a-967a-52639d137eb6}" \
    --initial-sync
