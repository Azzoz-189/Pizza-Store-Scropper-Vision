# Tracking Service Dockerfile
FROM eaglevision-base:latest

WORKDIR /app

# Install tracking-specific dependencies
RUN pip install --no-cache-dir deep_sort_realtime

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
