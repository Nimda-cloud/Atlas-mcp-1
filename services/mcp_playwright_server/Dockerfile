FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=4005 \
    HEADLESS=true \
    NODE_TLS_REJECT_UNAUTHORIZED=0

# Set working directory
WORKDIR /app

# Install system dependencies required for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgbm1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    ca-certificates \
    xvfb \
    fonts-liberation \
    libappindicator3-1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with SSL workarounds
RUN pip install --upgrade pip && \
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org playwright || \
    pip install playwright

# Copy application first
COPY app.py /app/app.py

# Create a non-root user for security
RUN useradd -m -u 1000 playwright && \
    chown -R playwright:playwright /app

USER playwright

# Try to install browsers at runtime via entrypoint (lazy installation)
COPY --chown=playwright:playwright <<EOF /app/entrypoint.sh
#!/bin/bash
echo "Starting Playwright MCP Server..."

# Try to install browsers if not already installed (lazy installation)
if [ ! -d "\$HOME/.cache/ms-playwright" ]; then
    echo "Installing Playwright browsers (this may take a while on first run)..."
    export NODE_TLS_REJECT_UNAUTHORIZED=0
    playwright install chromium || echo "Browser installation failed, will use system browser if available"
fi

# Start the server
exec python /app/app.py
EOF

RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 4005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:4005/health || exit 1

# Run via entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
