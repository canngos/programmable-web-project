FROM python:3.11-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    postgresql-client

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies in virtual environment
COPY ticket_management_system/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser -D -u 1000 flaskuser

# Set up entrypoint
COPY ticket_management_system/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Change ownership of app and virtual environment
RUN chown -R flaskuser:flaskuser /app /opt/venv

# Switch to non-root user
USER flaskuser

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
