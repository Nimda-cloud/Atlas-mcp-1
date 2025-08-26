#!/bin/bash
# Автоматичне розгортання оригінальних MCP серверів з TBXark proxy
# Версія: 2.0 - ОРИГІНАЛЬНІ РЕПОЗИТОРІЇ

set -e

# Кольори для виводу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функція логування
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Перевірка системних вимог
check_system_requirements() {
    log "Перевірка системних вимог..."
    
    # macOS версія
    if [[ "$(uname)" != "Darwin" ]]; then
        error "Цей скрипт призначений тільки для macOS"
        exit 1
    fi
    
    # Homebrew
    if ! command -v brew &> /dev/null; then
        error "Homebrew не знайдено. Встановіть з https://brew.sh/"
        exit 1
    fi
    
    # Node.js
    if ! command -v node &> /dev/null; then
        warning "Node.js не знайдено. Встановлюємо..."
        brew install node@22
    fi
    
    # Python
    if ! command -v python3 &> /dev/null; then
        warning "Python3 не знайдено. Встановлюємо..."
        brew install python@3.12
    fi
    
    # Git
    if ! command -v git &> /dev/null; then
        error "Git не знайдено. Встановіть Git"
        exit 1
    fi
    
    # FFmpeg для TTS
    if ! command -v ffmpeg &> /dev/null; then
        warning "FFmpeg не знайдено. Встановлюємо..."
        brew install ffmpeg
    fi
    
    # Make для збірки proxy
    if ! command -v make &> /dev/null; then
        error "Make не знайдено. Встановіть Xcode Command Line Tools"
        exit 1
    fi
    
    success "Системні вимоги перевірено"
}

# Створення структури каталогів
create_directory_structure() {
    log "Створення структури каталогів..."
    
    local base_dir="$HOME/mcp-stack"
    
    # Основні каталоги
    mkdir -p "$base_dir"/{applescript,automator,automation,playwright,tts,vnc,proxy}
    mkdir -p "$base_dir/proxy"/{logs,config,build}
    mkdir -p "$base_dir/logs"
    mkdir -p "$base_dir/venvs"
    
    # Створення Python віртуального середовища для MCP серверів
    if [[ ! -d "$base_dir/venvs/mcp" ]]; then
        python3 -m venv "$base_dir/venvs/mcp"
        source "$base_dir/venvs/mcp/bin/activate"
        pip install --upgrade pip
        pip install mcp
        deactivate
    fi
    
    success "Структура каталогів створена: $base_dir"
}

# Встановлення AppleScript MCP (оригінальний від peakmojo)
install_applescript_mcp() {
    log "Встановлення AppleScript MCP (peakmojo/applescript-mcp)..."
    
    local install_dir="$HOME/mcp-stack/applescript"
    
    # Клонування оригінального репозиторію
    if [[ ! -d "$install_dir/applescript-mcp" ]]; then
        cd "$install_dir"
        git clone https://github.com/peakmojo/applescript-mcp.git
        cd applescript-mcp
        
        # Встановлення залежностей
        npm install
        
        # Тестування
        if node dist/index.js --version &>/dev/null; then
            success "AppleScript MCP встановлено успішно"
        else
            warning "AppleScript MCP може потребувати додаткової конфігурації"
        fi
    else
        success "AppleScript MCP вже встановлено"
    fi
    
    # Створення wrapper скрипта
    cat > "$install_dir/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/applescript-mcp"
exec node dist/index.js
EOF
    chmod +x "$install_dir/start.sh"
}

# Встановлення macOS Automator MCP (оригінальний від steipete)
install_automator_mcp() {
    log "Встановлення macOS Automator MCP (steipete/macos-automator-mcp)..."
    
    local install_dir="$HOME/mcp-stack/automator"
    
    if [[ ! -d "$install_dir/macos-automator-mcp" ]]; then
        cd "$install_dir"
        git clone https://github.com/steipete/macos-automator-mcp.git
        cd macos-automator-mcp
        
        # Встановлення залежностей
        npm install
        npm run build
        
        success "macOS Automator MCP встановлено успішно"
    else
        success "macOS Automator MCP вже встановлено"
    fi
    
    # Wrapper скрипт
    cat > "$install_dir/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/macos-automator-mcp"
exec node dist/index.js
EOF
    chmod +x "$install_dir/start.sh"
}

# Встановлення Automation MCP (оригінальний від ashwwwin)
install_automation_mcp() {
    log "Встановлення Automation MCP (ashwwwin/automation-mcp)..."
    
    local install_dir="$HOME/mcp-stack/automation"
    local venv_path="$HOME/mcp-stack/venvs/mcp"
    
    if [[ ! -d "$install_dir/automation-mcp" ]]; then
        cd "$install_dir"
        git clone https://github.com/ashwwwin/automation-mcp.git
        cd automation-mcp
        
        # Активація віртуального середовища та встановлення
        source "$venv_path/bin/activate"
        pip install -e .
        deactivate
        
        success "Automation MCP встановлено успішно"
    else
        success "Automation MCP вже встановлено"
    fi
    
    # Wrapper скрипт для Python
    cat > "$install_dir/start.sh" << EOF
#!/bin/bash
source "$venv_path/bin/activate"
cd "\$(dirname "\$0")/automation-mcp"
exec python -m automation_mcp
EOF
    chmod +x "$install_dir/start.sh"
}

# Встановлення Playwright MCP (офіційний від Microsoft)
install_playwright_mcp() {
    log "Встановлення Playwright MCP (Microsoft/playwright-mcp)..."
    
    local install_dir="$HOME/mcp-stack/playwright"
    local venv_path="$HOME/mcp-stack/venvs/mcp"
    
    if [[ ! -d "$install_dir/playwright-mcp" ]]; then
        cd "$install_dir"
        git clone https://github.com/microsoft/playwright-mcp.git
        cd playwright-mcp
        
        # Активація віртуального середовища
        source "$venv_path/bin/activate"
        pip install -e .
        
        # Встановлення браузерів
        playwright install
        deactivate
        
        success "Playwright MCP встановлено успішно"
    else
        success "Playwright MCP вже встановлено"
    fi
    
    # Wrapper скрипт
    cat > "$install_dir/start.sh" << EOF
#!/bin/bash
source "$venv_path/bin/activate"
cd "\$(dirname "\$0")/playwright-mcp"
exec python -m playwright_mcp
EOF
    chmod +x "$install_dir/start.sh"
}

# Встановлення TTS MCP (оригінальний від hmage)
install_tts_mcp() {
    log "Встановлення TTS MCP (hmage/mcp-tts)..."
    
    local install_dir="$HOME/mcp-stack/tts"
    local venv_path="$HOME/mcp-stack/venvs/mcp"
    
    if [[ ! -d "$install_dir/mcp-tts" ]]; then
        cd "$install_dir"
        git clone https://github.com/hmage/mcp-tts.git
        cd mcp-tts
        
        # Активація віртуального середовища
        source "$venv_path/bin/activate"
        pip install -r requirements.txt
        deactivate
        
        success "TTS MCP встановлено успішно"
    else
        success "TTS MCP вже встановлено"
    fi
    
    # TTS MCP підтримує HTTP режим
    cat > "$install_dir/start_http.sh" << EOF
#!/bin/bash
source "$venv_path/bin/activate"
cd "\$(dirname "\$0")/mcp-tts"
exec python server.py --port 4001
EOF
    chmod +x "$install_dir/start_http.sh"
    
    # Спроба stdio режиму (якщо підтримується)
    cat > "$install_dir/start.sh" << EOF
#!/bin/bash
source "$venv_path/bin/activate"
cd "\$(dirname "\$0")/mcp-tts"
exec python server.py --stdio
EOF
    chmod +x "$install_dir/start.sh"
}

# Встановлення VNC MCP (оригінальний від hrrrsn)
install_vnc_mcp() {
    log "Встановлення VNC MCP (hrrrsn/mcp-vnc)..."
    
    local install_dir="$HOME/mcp-stack/vnc"
    local venv_path="$HOME/mcp-stack/venvs/mcp"
    
    if [[ ! -d "$install_dir/mcp-vnc" ]]; then
        cd "$install_dir"
        git clone https://github.com/hrrrsn/mcp-vnc.git
        cd mcp-vnc
        
        # Активація віртуального середовища
        source "$venv_path/bin/activate"
        pip install -e .
        deactivate
        
        success "VNC MCP встановлено успішно"
    else
        success "VNC MCP вже встановлено"
    fi
    
    # Wrapper скрипт
    cat > "$install_dir/start.sh" << EOF
#!/bin/bash
source "$venv_path/bin/activate"
cd "\$(dirname "\$0")/mcp-vnc"
exec python -m mcp_vnc
EOF
    chmod +x "$install_dir/start.sh"
}

# Встановлення TBXark mcp-proxy
install_tbxark_proxy() {
    log "Встановлення TBXark mcp-proxy..."
    
    local install_dir="$HOME/mcp-stack/proxy"
    
    if [[ ! -d "$install_dir/mcp-proxy" ]]; then
        cd "$install_dir"
        git clone https://github.com/TBXark/mcp-proxy.git
        cd mcp-proxy
        
        # Збірка proxy
        make build
        
        if [[ -f "build/mcp-proxy" ]]; then
            success "TBXark mcp-proxy зібрано успішно"
        else
            error "Помилка збірки mcp-proxy"
            exit 1
        fi
    else
        success "TBXark mcp-proxy вже встановлено"
    fi
}

# Створення конфігурації proxy з гнучким підключенням
create_flexible_proxy_config() {
    log "Створення гнучкої конфігурації mcp-proxy..."
    
    local config_file="$HOME/mcp-stack/proxy/config.json"
    
    cat > "$config_file" << 'EOF'
{
  "server": {
    "host": "127.0.0.1",
    "port": 4010
  },
  "logging": {
    "level": "info",
    "file": "logs/mcp-proxy.log"
  },
  "clients": [
    {
      "name": "applescript",
      "type": "stdio",
      "command": "bash",
      "args": ["/Users/$(whoami)/mcp-stack/applescript/start.sh"],
      "env": {},
      "timeout": 30
    },
    {
      "name": "automator", 
      "type": "stdio",
      "command": "bash",
      "args": ["/Users/$(whoami)/mcp-stack/automator/start.sh"],
      "env": {},
      "timeout": 30
    },
    {
      "name": "automation",
      "type": "stdio", 
      "command": "bash",
      "args": ["/Users/$(whoami)/mcp-stack/automation/start.sh"],
      "env": {},
      "timeout": 30
    },
    {
      "name": "playwright",
      "type": "stdio",
      "command": "bash", 
      "args": ["/Users/$(whoami)/mcp-stack/playwright/start.sh"],
      "env": {},
      "timeout": 30
    },
    {
      "name": "tts_stdio",
      "type": "stdio",
      "command": "bash",
      "args": ["/Users/$(whoami)/mcp-stack/tts/start.sh"],
      "env": {},
      "timeout": 30,
      "fallback": {
        "name": "tts_http",
        "type": "http",
        "url": "http://127.0.0.1:4001",
        "startup_command": "bash /Users/$(whoami)/mcp-stack/tts/start_http.sh"
      }
    },
    {
      "name": "vnc",
      "type": "stdio",
      "command": "bash",
      "args": ["/Users/$(whoami)/mcp-stack/vnc/start.sh"], 
      "env": {},
      "timeout": 30
    }
  ],
  "features": {
    "namespacing": true,
    "audit_logging": true,
    "health_checks": true,
    "fallback_chain": true
  }
}
EOF

    # Замінити $(whoami) на реальне ім'я користувача
    local username=$(whoami)
    sed -i "" "s/\$(whoami)/$username/g" "$config_file"
    
    success "Конфігурація proxy створена: $config_file"
}

# Створення скрипта управління стеком
create_management_script() {
    log "Створення скрипта управління MCP стеком..."
    
    cat > "$HOME/mcp-stack/manage.sh" << 'EOF'
#!/bin/bash
# Управління MCP стеком

MCP_DIR="$HOME/mcp-stack"
PROXY_DIR="$MCP_DIR/proxy/mcp-proxy"
CONFIG_FILE="$MCP_DIR/proxy/config.json"
PID_FILE="$MCP_DIR/proxy.pid"

case "$1" in
    start)
        echo "Запуск MCP proxy..."
        cd "$PROXY_DIR"
        nohup ./build/mcp-proxy --config "$CONFIG_FILE" > "$MCP_DIR/logs/proxy.log" 2>&1 &
        echo $! > "$PID_FILE"
        echo "MCP proxy запущено (PID: $(cat $PID_FILE))"
        ;;
    stop)
        if [[ -f "$PID_FILE" ]]; then
            PID=$(cat "$PID_FILE")
            echo "Зупинка MCP proxy (PID: $PID)..."
            kill "$PID" 2>/dev/null || true
            rm -f "$PID_FILE"
            echo "MCP proxy зупинено"
        else
            echo "MCP proxy не запущено"
        fi
        ;;
    status)
        if [[ -f "$PID_FILE" ]] && kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
            echo "MCP proxy працює (PID: $(cat $PID_FILE))"
            echo "Health check..."
            curl -s http://127.0.0.1:4010/health || echo "Health check failed"
        else
            echo "MCP proxy не працює"
        fi
        ;;
    logs)
        tail -f "$MCP_DIR/logs/proxy.log"
        ;;
    test)
        echo "Тестування MCP proxy..."
        curl -X POST http://127.0.0.1:4010 \
             -H "Content-Type: application/json" \
             -d '{"jsonrpc":"2.0","id":"test","method":"list_tools"}' | jq
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    *)
        echo "Використання: $0 {start|stop|status|logs|test|restart}"
        exit 1
        ;;
esac
EOF

    chmod +x "$HOME/mcp-stack/manage.sh"
    success "Скрипт управління створено: $HOME/mcp-stack/manage.sh"
}

# Головна функція розгортання
main() {
    log "=== РОЗГОРТАННЯ ОРИГІНАЛЬНИХ MCP СЕРВЕРІВ ==="
    log "Дата: $(date)"
    log "Користувач: $(whoami)"
    log "Система: $(uname -a)"
    
    # Перевірка прав root
    if [[ $EUID -eq 0 ]]; then
        error "Не запускайте цей скрипт від root!"
        exit 1
    fi
    
    # Послідовне виконання етапів
    check_system_requirements
    create_directory_structure
    
    log "=== ВСТАНОВЛЕННЯ MCP СЕРВЕРІВ ==="
    install_applescript_mcp
    install_automator_mcp
    install_automation_mcp
    install_playwright_mcp
    install_tts_mcp
    install_vnc_mcp
    
    log "=== ВСТАНОВЛЕННЯ PROXY ==="
    install_tbxark_proxy
    create_flexible_proxy_config
    create_management_script
    
    success "=== РОЗГОРТАННЯ ЗАВЕРШЕНО ==="
    log "Для запуску використовуйте:"
    log "  $HOME/mcp-stack/manage.sh start"
    log "  $HOME/mcp-stack/manage.sh status"
    log "  $HOME/mcp-stack/manage.sh test"
    
    # Автоматичний запуск для тестування
    if [[ "$2" == "--start" ]]; then
        log "Автоматичний запуск MCP стека..."
        "$HOME/mcp-stack/manage.sh" start
        sleep 3
        "$HOME/mcp-stack/manage.sh" status
    fi
}

# Запуск з обробкою помилок
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
