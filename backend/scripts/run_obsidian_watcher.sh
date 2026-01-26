#!/bin/bash
# Wrapper script for obsidian watcher that loads .env variables

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
    -m scripts.obsidian_watcher \
    --user-id "${OBSIDIAN_USER_ID:-4d957e43-b34f-456a-967a-52639d137eb6}" \
    --initial-sync
