#!/bin/bash

# A script to run the full document intelligence pipeline.
# It runs service1a to extract outlines, then runs service1b to rank them.

# --- Configuration ---
# You can change the default query here or pass it as an argument to the script.
DEFAULT_QUERY="What are the key dates, submission deadlines, and topics?"
USER_QUERY="${1:-$DEFAULT_QUERY}" # Use the first script argument or the default query

# Stop on any error
set -e

echo "--- Building Docker images... ---"
docker-compose build

echo -e "\n--- Running Service 1a (Outline Extraction)... ---"
# 'run --rm' creates a container, runs the command, and removes it upon completion.
docker-compose run --rm service1a

echo -e "\n✅ Service 1a finished. Outlines are now available in the shared volume."
echo "--- Running Service 1b (Persona-based Ranking)... ---"
echo "Using Query: '$USER_QUERY'"

# Run service1b and pass the user query to it.
docker-compose run --rm service1b "$USER_QUERY"

echo -e "\n✅ Pipeline finished successfully! ---"
echo "Check the 'service1b/output' directory for the final ranked results."
