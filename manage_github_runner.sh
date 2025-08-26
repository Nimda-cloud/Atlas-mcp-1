#!/bin/bash

# GitHub Actions Runner Management Script
# Автор: Atlas Development Team
# Дата: $(date)

RUNNER_DIR="/Users/dev/actions-runner"
REPO_DIR="/Users/dev/Documents/Atlas-mcp"

# Кольори для виводу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_runner_status() {
    echo_info "Перевіряємо статус GitHub Actions Runner..."
    
    if [ -d "$RUNNER_DIR" ]; then
        cd "$RUNNER_DIR"
        
        # Перевіряємо чи запущена служба
        if launchctl list | grep -q "actions.runner.Nimda-cloud-Atlas-mcp-1.DEVs-Mac-Studio"; then
            echo_success "GitHub Actions Runner запущений"
            
            # Показуємо статус
            echo_info "Статус служби:"
            launchctl list | grep "actions.runner"
            
            return 0
        else
            echo_warning "GitHub Actions Runner не запущений"
            return 1
        fi
    else
        echo_error "Директорія runner'а не знайдена: $RUNNER_DIR"
        return 1
    fi
}

start_runner() {
    echo_info "Запускаємо GitHub Actions Runner..."
    
    if [ ! -d "$RUNNER_DIR" ]; then
        echo_error "Директорія runner'а не знайдена: $RUNNER_DIR"
        echo_info "Спершу налаштуйте runner за допомогою setup_runner_service.sh"
        return 1
    fi
    
    cd "$RUNNER_DIR"
    
    # Запускаємо службу
    ./svc.sh start
    
    if [ $? -eq 0 ]; then
        echo_success "GitHub Actions Runner успішно запущений"
        
        # Чекаємо підключення
        echo_info "Чекаємо підключення до GitHub..."
        sleep 5
        
        check_runner_status
    else
        echo_error "Помилка запуску GitHub Actions Runner"
        return 1
    fi
}

stop_runner() {
    echo_info "Зупиняємо GitHub Actions Runner..."
    
    if [ ! -d "$RUNNER_DIR" ]; then
        echo_error "Директорія runner'а не знайдена: $RUNNER_DIR"
        return 1
    fi
    
    cd "$RUNNER_DIR"
    
    # Зупиняємо службу
    ./svc.sh stop
    
    if [ $? -eq 0 ]; then
        echo_success "GitHub Actions Runner успішно зупинений"
    else
        echo_error "Помилка зупинки GitHub Actions Runner"
        return 1
    fi
}

restart_runner() {
    echo_info "Перезапускаємо GitHub Actions Runner..."
    
    stop_runner
    sleep 3
    start_runner
}

show_logs() {
    echo_info "Показуємо логи GitHub Actions Runner..."
    
    LOG_FILE="/Users/dev/Library/Logs/actions.runner.Nimda-cloud-Atlas-mcp-1.DEVs-Mac-Studio/actions.runner.Nimda-cloud-Atlas-mcp-1.DEVs-Mac-Studio.log"
    
    if [ -f "$LOG_FILE" ]; then
        echo_info "Останні 50 рядків логу:"
        tail -n 50 "$LOG_FILE"
    else
        echo_warning "Лог файл не знайдений: $LOG_FILE"
    fi
}

show_runner_info() {
    echo_info "Інформація про GitHub Actions Runner:"
    echo ""
    echo "Директорія runner'а: $RUNNER_DIR"
    echo "Директорія проекту: $REPO_DIR"
    echo "Репозиторій: Nimda-cloud/Atlas-mcp-1"
    echo ""
    
    if [ -d "$RUNNER_DIR" ]; then
        cd "$RUNNER_DIR"
        
        echo "Версія runner'а:"
        if [ -f ".runner" ]; then
            cat .runner | head -5
        fi
        echo ""
        
        echo "Конфігурація:"
        if [ -f ".credentials" ]; then
            echo "✅ Credentials файл існує"
        else
            echo "❌ Credentials файл відсутній"
        fi
        
        if [ -f ".service" ]; then
            echo "✅ Service файл існує"
        else
            echo "❌ Service файл відсутній"
        fi
    fi
}

run_test_workflow() {
    echo_info "Запускаємо тестовий workflow..."
    
    cd "$REPO_DIR"
    
    # Перевіряємо чи існує основний workflow
    if [ -f ".github/workflows/test-and-merge.yml" ]; then
        echo_success "Workflow файл знайдений"
        
        echo_info "Для запуску workflow виконайте команду:"
        echo "gh workflow run test-and-merge.yml"
        echo ""
        echo "Або зробіть commit і push до main гілки"
    else
        echo_error "Workflow файл не знайдений: .github/workflows/test-and-merge.yml"
    fi
}

show_help() {
    echo "GitHub Actions Runner Management Script"
    echo "======================================"
    echo ""
    echo "Використання: $0 [КОМАНДА]"
    echo ""
    echo "Команди:"
    echo "  start     - Запустити GitHub Actions Runner"
    echo "  stop      - Зупинити GitHub Actions Runner"
    echo "  restart   - Перезапустити GitHub Actions Runner"
    echo "  status    - Показати статус runner'а"
    echo "  logs      - Показати логи runner'а"
    echo "  info      - Показати інформацію про runner"
    echo "  test      - Запустити тестовий workflow"
    echo "  help      - Показати цю довідку"
    echo ""
    echo "Приклади:"
    echo "  $0 start    # Запустити runner"
    echo "  $0 status   # Перевірити статус"
    echo "  $0 logs     # Подивитися логи"
}

# Основна логіка
case "$1" in
    start)
        start_runner
        ;;
    stop)
        stop_runner
        ;;
    restart)
        restart_runner
        ;;
    status)
        check_runner_status
        ;;
    logs)
        show_logs
        ;;
    info)
        show_runner_info
        ;;
    test)
        run_test_workflow
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        echo_info "GitHub Actions Runner Management"
        echo ""
        check_runner_status
        echo ""
        echo "Використайте '$0 help' для отримання довідки"
        ;;
    *)
        echo_error "Невідома команда: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
