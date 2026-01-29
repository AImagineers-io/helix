FROM python:3.11-slim-bookworm

WORKDIR /app

# Install PostgreSQL client tools (needed for database operations)
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY 02_backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY 02_backend/ .

# Copy version.json from project root
COPY version.json /version.json

# Expose port
EXPOSE 8000

# Run uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
