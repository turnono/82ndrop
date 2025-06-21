# Use Python 3.11 slim image for better compatibility with ADK
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install problematic packages first (ADK dependency conflict resolution)
RUN pip install --no-cache-dir google-cloud-aiplatform==1.71.1
RUN pip install --no-cache-dir google-adk==1.4.1

# Install remaining requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Copy Firebase service account credentials
COPY taajirah-agents-service-account.json ./
COPY drop_agent/taajirah-agents-service-account.json ./drop_agent/

# Create logs directory for analytics
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Set environment variables
ENV PORT=8000
ENV PYTHONPATH=/app
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/taajirah-agents-service-account.json

# Run the application
CMD ["python", "main.py"] 