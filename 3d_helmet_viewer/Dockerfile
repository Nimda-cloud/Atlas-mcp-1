FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements for the enhanced frontend
COPY requirements-frontend.txt .
RUN pip install --no-cache-dir -r requirements-frontend.txt

# Copy frontend files
COPY enhanced_frontend_simple.html .
COPY enhanced_server.py .
COPY DamagedHelmet.glb .
COPY *.html .

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the enhanced server
CMD ["python", "enhanced_server.py"]