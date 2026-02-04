#!/bin/bash
# Wrapper script for vault watcher that loads .env variables via dotenvx
#
# NOTE: The vault watcher now starts automatically with the backend server
# when VAULT_WATCHER_USER_ID is configured. This script is for manual/standalone use
# or for running via launchd.

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$BACKEND_DIR"

# Load the dotenvx private key from .env.keys if it exists (skip comments)
if [ -f .env.keys ]; then
    DOTENV_PRIVATE_KEY=$(grep -E '^DOTENV_PRIVATE_KEY=' .env.keys | cut -d'=' -f2- | tr -d '"')
    export DOTENV_PRIVATE_KEY
fi

# Default private key (fallback)
DOTENV_PRIVATE_KEY="${DOTENV_PRIVATE_KEY:-4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230}"
export DOTENV_PRIVATE_KEY

# Run the watcher with dotenvx for env decryption
# Use full path to dotenvx for launchd compatibility
exec /opt/homebrew/bin/dotenvx run -f .env -- "$BACKEND_DIR/.venv/bin/python" \
    -m scripts.vault_watcher \
    --user-id "${VAULT_WATCHER_USER_ID:-4d957e43-b34f-456a-967a-52639d137eb6}" \
    --initial-sync
