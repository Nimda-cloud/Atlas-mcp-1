#!/bin/bash

# Ukrainian TTS MCP Server Startup Script

# Перехід до директорії
cd "$(dirname "$0")"

# Перевірка віртуального середовища
VENV_PATH="../atlas_venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Активація віртуального середовища
source "$VENV_PATH/bin/activate"

# Установка залежностей
echo "📦 Installing Ukrainian TTS dependencies..."
pip install -q ukrainian-tts[all] gtts pygame mcp fastapi uvicorn requests pydantic aiofiles

# Запуск MCP сервера
echo "🎙️ Starting Ukrainian TTS MCP Server..."
python mcp_tts_server.py
