# Minimal Alpine Python
FROM python:3.11-alpine

WORKDIR /app

# Install only essential dependencies
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    postgresql-dev \
    && apk add --no-cache postgresql-client

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

COPY . .

# Use a non-root user
RUN adduser -D -u 1000 flaskuser && chown -R flaskuser:flaskuser /app
USER flaskuser

EXPOSE 5000

CMD ["python", "app.py"]