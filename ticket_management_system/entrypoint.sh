#!/bin/sh
set -e

echo "=== Starting Flask Application ==="

# Clear Python bytecode cache to ensure fresh imports
echo "Clearing Python cache..."
find /app/ticket_management_system -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find /app/ticket_management_system -type f -name "*.pyc" -delete 2>/dev/null || true

FLASK_APP_TARGET="ticket_management_system.app:app"

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 0.5
done
echo "PostgreSQL is ready!"

# Check if migrations directory exists
MIGRATIONS_DIR="/app/ticket_management_system/migrations"
if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo "Initializing migrations..."
    cd /app && PYTHONPATH=/app flask --app "$FLASK_APP_TARGET" db init
fi

# Run migrations
echo "Running database migrations..."
cd /app && PYTHONPATH=/app flask --app "$FLASK_APP_TARGET" db upgrade

# Start application with Gunicorn configuration
echo "Starting Gunicorn..."
exec gunicorn --config /app/ticket_management_system/gunicorn_config.py ticket_management_system.app:app
