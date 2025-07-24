# Base image with lightweight Python and CPU-only PyTorch for CV microservices
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy common requirements (will install manually)
COPY docker/common-requirements.txt ./

# Skip pip install - will do manually inside container
# Install CPU-only PyTorch first (much smaller than CUDA version)
# RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
# RUN pip install --no-cache-dir -r common-requirements.txt

# This base image can be extended by specific services
CMD ["bash"]
