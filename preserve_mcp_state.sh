#!/bin/bash

# 🔄 Atlas MCP State Preservation Script
# Зберігає поточний стан повністю функціонального MCP stack

echo "🛡️ Зберігаю поточний стан Atlas MCP Stack..."

# Створюємо директорію для збереження стану
BACKUP_DIR="/Users/dev/Documents/Atlas-mcp/mcp_state_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📁 Створено директорію: $BACKUP_DIR"

# Зберігаємо конфігурацію MCP proxy
echo "💾 Зберігаю конфігурацію MCP proxy..."
cp /Users/dev/mcp-stack/proxy/config.json "$BACKUP_DIR/proxy_config.json"

# Зберігаємо всі start.sh скрипти
echo "🚀 Зберігаю start.sh скрипти..."
mkdir -p "$BACKUP_DIR/start_scripts"
cp /Users/dev/mcp-stack/tts/start.sh "$BACKUP_DIR/start_scripts/tts_start.sh"
cp /Users/dev/mcp-stack/automation/start.sh "$BACKUP_DIR/start_scripts/automation_start.sh"
cp /Users/dev/mcp-stack/automator/start.sh "$BACKUP_DIR/start_scripts/automator_start.sh"
cp /Users/dev/mcp-stack/applescript/start.sh "$BACKUP_DIR/start_scripts/applescript_start.sh"
cp /Users/dev/mcp-stack/vnc/start.sh "$BACKUP_DIR/start_scripts/vnc_start.sh"
cp /Users/dev/mcp-stack/playwright/start.sh "$BACKUP_DIR/start_scripts/playwright_start.sh"

# Створюємо звіт про поточний стан
echo "📊 Створюю звіт про стан MCP сервісів..."
cat > "$BACKUP_DIR/mcp_state_report.md" << 'EOF'
# 🎯 Atlas MCP Stack - Повний Стан

## ✅ Успішно Підключені Сервіси (6/6)

### 1. TTS Service - 4 інструменти
- elevenlabs_tts
- google_tts  
- openai_tts
- say_tts

### 2. Automation Service - 20 інструментів
- mouseClick, mouseDoubleClick, mouseMove
- mouseGetPosition, mouseScroll, mouseDrag
- mouseButtonControl, type, keyControl
- screenshot, screenInfo, screenHighlight
- colorAt, getWindows, getActiveWindow
- windowControl, waitForImage, sleep
- mouseMovePath, systemCommand

### 3. Automator Service - 2 інструменти
- execute_script
- get_scripting_tips

### 4. AppleScript Service - 1 інструмент
- applescript_execute

### 5. VNC Service - 6 інструментів
- vnc_click, vnc_move_mouse, vnc_key_press
- vnc_type_text, vnc_type_multiline, vnc_screenshot

### 6. Playwright Service - 21 інструмент ✅ (ВИПРАВЛЕНО!)
- browser_close, browser_resize, browser_console_messages
- browser_handle_dialog, browser_evaluate, browser_file_upload
- browser_fill_form, browser_install, browser_press_key
- browser_type, browser_navigate, browser_navigate_back
- browser_network_requests, browser_take_screenshot, browser_snapshot
- browser_click, browser_drag, browser_hover
- browser_select_option, browser_tabs, browser_wait_for

## 🔧 Ключові Виправлення

1. **Playwright Service**: Змінено start.sh з `index.js` на `cli.js`
2. **Всі сервіси**: Виправлені шляхи в start.sh скриптах
3. **MCP Proxy**: Налаштований на порт 4010 з правильною конфігурацією

## 📈 Статистика
- **Загальна кількість інструментів**: 54
- **Активні сервіси**: 6/6 (100%)
- **MCP Proxy**: localhost:4010
- **Статус**: ПОВНІСТЮ ФУНКЦІОНАЛЬНИЙ ✅

## 🚀 Команди Запуску

### Запуск MCP Proxy:
```bash
cd /Users/dev/mcp-stack/proxy && ./mcp-proxy/build/mcp-proxy
```

### Запуск Atlas з MCP режимом:
```bash
cd /Users/dev/Documents/Atlas-mcp
export ATLAS_MCP_PROXY_MODE=true
export ATLAS_MCP_PROXY_URL=http://localhost:4010
source atlas_venv/bin/activate
python atlas_core.py
```

## 🎯 Ukrainian TTS Integration
- Модель: robinhad/ukrainian-tts
- Голос: mykyta, dictionary
- Статус: Повністю інтегровано ✅
EOF

# Зберігаємо поточні процеси
echo "🔍 Записую поточні процеси..."
ps aux | grep -E "(mcp-proxy|node.*cli.js|atlas_core)" | grep -v grep > "$BACKUP_DIR/current_processes.txt"

# Зберігаємо статус портів
echo "🌐 Записую статус портів..."
lsof -i :4010 > "$BACKUP_DIR/port_4010_status.txt" 2>/dev/null || echo "Port 4010 not in use" > "$BACKUP_DIR/port_4010_status.txt"

echo "✅ Стан збережено в: $BACKUP_DIR"
echo "📝 Звіт доступний: $BACKUP_DIR/mcp_state_report.md"

# Створюємо швидкий скрипт відновлення
cat > "$BACKUP_DIR/restore_mcp_state.sh" << 'EOF'
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
EOF

chmod +x "$BACKUP_DIR/restore_mcp_state.sh"

echo "🎯 Готово! Стан MCP Stack збережено та готовий до використання."
