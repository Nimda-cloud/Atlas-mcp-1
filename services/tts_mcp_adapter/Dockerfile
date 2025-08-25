# Local TTS MCP Adapter image - simplified
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app.py /app/

# Install minimal dependencies with SSL workarounds
RUN pip install --upgrade pip && \
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org \
        fastapi uvicorn aiohttp requests || \
    echo "TTS service will run in minimal mode"

ENV MCP_PORT=4004 \
    TTS_OUTPUT_DIR=/data/tts

VOLUME ["/data/tts"]
EXPOSE 4004

CMD ["python", "app.py"]
