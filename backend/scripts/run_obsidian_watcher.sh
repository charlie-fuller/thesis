#!/bin/bash
# Wrapper script for obsidian watcher that loads .env variables

cd /Users/charlie.fuller/vaults/Contentful/thesis/backend

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
fi

# Run the watcher with initial sync
exec /Users/charlie.fuller/vaults/Contentful/thesis/backend/.venv/bin/python \
    -m scripts.obsidian_watcher \
    --user-id 4d957e43-b34f-456a-967a-52639d137eb6 \
    --initial-sync
