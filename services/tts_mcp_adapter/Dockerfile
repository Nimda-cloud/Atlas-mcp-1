# Local TTS MCP Adapter image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py /app/

ENV MCP_PORT=4004 \
    TTS_OUTPUT_DIR=/data/tts

VOLUME ["/data/tts"]
EXPOSE 4004

CMD ["python", "app.py"]
