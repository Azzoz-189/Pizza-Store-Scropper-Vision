# Detection Service Dockerfile
# Use common base image with pre-installed PyTorch and dependencies
FROM eaglevision-base:latest

WORKDIR /app

# Copy the application code first
COPY . .

# Install the package in development mode (editable)
RUN pip install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV MODEL_WEIGHTS=/app/models/yolo12m-v2.pt

# Create models directory if it doesn't exist
RUN mkdir -p /app/models

# Use the module path that matches your directory structure
CMD ["uvicorn", "detection.main:app", "--host", "0.0.0.0", "--port", "8001"]
