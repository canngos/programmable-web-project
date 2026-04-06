#!/bin/sh
set -e

echo "=== Starting Flask Application ==="

FLASK_APP_TARGET="app:app"

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 0.5
done
echo "PostgreSQL is ready!"

# Run migration commands from the package directory so Flask-Migrate uses
# ticket_management_system/migrations as its default location.
MIGRATIONS_DIR="/app/ticket_management_system/migrations"
if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo "Initializing migrations..."
    (cd /app/ticket_management_system && PYTHONPATH=/app flask --app "$FLASK_APP_TARGET" db init)
fi

# Run migrations
echo "Running database migrations..."
(cd /app/ticket_management_system && PYTHONPATH=/app flask --app "$FLASK_APP_TARGET" db upgrade)

# Start application with Gunicorn configuration
echo "Starting Gunicorn..."
exec gunicorn --config /app/ticket_management_system/gunicorn_config.py ticket_management_system.app:app
