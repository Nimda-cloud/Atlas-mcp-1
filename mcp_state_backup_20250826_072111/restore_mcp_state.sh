#!/bin/bash
echo "🔄 Відновлюю MCP Stack стан..."

# Відновлюємо конфігурації
cp proxy_config.json /Users/dev/mcp-stack/proxy/config.json

# Відновлюємо start.sh скрипти
cp start_scripts/tts_start.sh /Users/dev/mcp-stack/tts/start.sh
cp start_scripts/automation_start.sh /Users/dev/mcp-stack/automation/start.sh
cp start_scripts/automator_start.sh /Users/dev/mcp-stack/automator/start.sh
cp start_scripts/applescript_start.sh /Users/dev/mcp-stack/applescript/start.sh
cp start_scripts/vnc_start.sh /Users/dev/mcp-stack/vnc/start.sh
cp start_scripts/playwright_start.sh /Users/dev/mcp-stack/playwright/start.sh

# Робимо скрипти виконуваними
chmod +x /Users/dev/mcp-stack/*/start.sh

echo "✅ MCP Stack стан відновлено!"
echo "Запустіть: cd /Users/dev/mcp-stack/proxy && ./mcp-proxy/build/mcp-proxy"
