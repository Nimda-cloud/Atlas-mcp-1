#!/bin/bash
# Запуск 3D Helmet Viewer
# Створено: GitHub Copilot для Atlas MCP

echo "🤖 Запуск 3D Helmet Viewer..."
echo "📁 Робоча директорія: $(pwd)"

# Перевірка наявності Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python не знайдено! Встановіть Python 3.x"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "🐍 Використовується: $PYTHON_CMD"

# Перевірка наявності файлів
if [[ ! -f "3d_viewer.html" ]]; then
    echo "❌ Файл 3d_viewer.html не знайдено!"
    exit 1
fi

if [[ ! -f "DamagedHelmet.glb" ]]; then
    echo "❌ Файл DamagedHelmet.glb не знайдено!"
    exit 1
fi

if [[ ! -f "start_3d_viewer.py" ]]; then
    echo "❌ Файл start_3d_viewer.py не знайдено!"
    exit 1
fi

echo "✅ Всі файли знайдено"
echo ""
echo "🚀 Запуск HTTP сервера..."
echo "🌐 Відкрийте http://localhost:8080/3d_viewer.html"
echo "⏹️  Натисніть Ctrl+C для зупинки"
echo ""

# Запуск сервера
$PYTHON_CMD start_3d_viewer.py
