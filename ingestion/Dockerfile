# Ingestion Service Dockerfile
# Use common base image with pre-installed dependencies
FROM eaglevision-base:latest

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and set up the working directory
RUN adduser --disabled-password --gecos "" appuser && \
    mkdir -p /app/video_samples && \
    chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Copy requirements first to leverage Docker cache
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install python-multipart

# Copy the application code
COPY . .

# Set environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
