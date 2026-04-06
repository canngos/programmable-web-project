#!/bin/sh
# Docker healthcheck script for Flask application
# This checks if the Flask app is running and responding to requests

set -e

MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # Try to connect to the app and check the /health endpoint
    if curl -f -s -m 5 http://localhost:5000/health > /dev/null 2>&1; then
        echo "Health check passed"
        exit 0
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        sleep 1
    fi
done

echo "Health check failed after $MAX_RETRIES attempts"
exit 1
