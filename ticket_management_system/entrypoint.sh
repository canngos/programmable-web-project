#!/bin/sh
set -e

echo "=== Starting Flask Application ==="

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 0.5
done
echo "PostgreSQL is ready!"

# Check if migrations folder exists
if [ ! -d "ticket_management_system/migrations" ]; then
    echo "Initializing migrations..."
    flask db --directory ticket_management_system/migrations init
fi

# Run migrations
echo "Running database migrations..."
flask db --directory ticket_management_system/migrations upgrade

# Start application
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 --access-logfile - ticket_management_system.app:app
