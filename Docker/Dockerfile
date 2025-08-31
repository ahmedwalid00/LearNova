FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

ENV PYTHONPATH=/app

# Create directory for Celery beat schedule
RUN mkdir -p /app/celerybeat

# Default command (will be overridden by docker-compose)
CMD ["python", "-m", "celery", "worker", "-A", "src.celery_app"]
