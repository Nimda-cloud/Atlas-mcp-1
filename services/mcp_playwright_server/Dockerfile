FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=4005 \
    PW_HEADLESS=true

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
            libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1 libxcomposite1 \
            libxdamage1 libxfixes3 libxrandr2 libasound2 libpangocairo-1.0-0 libgtk-3-0 \
            ca-certificates curl && \
        rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt && \
        python -m playwright install chromium

COPY app.py /app/app.py

EXPOSE 4005

CMD ["python", "/app/app.py"]
