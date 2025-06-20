FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the drop_agent module from root directory
COPY drop_agent ./drop_agent

# Copy the API code
COPY api/main.py .
COPY api/logging_config.py .
COPY api/middleware.py .
COPY api/taajirah-agents-service-account.json .

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/taajirah-agents-service-account.json

# Expose port
EXPOSE 8080

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"] 