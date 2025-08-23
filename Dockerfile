# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies including audio libraries
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    libsndfile1 \
    libsox-fmt-all \
    sox \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Spleeter models during build
RUN python -c "from spleeter.separator import Separator; Separator('spleeter:2stems-16kHz')"

# Copy application files
COPY . .

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run the processing service
CMD ["python", "processing_service.py"]