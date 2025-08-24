#!/bin/bash

# Atlas Autonomous System - Restart Script
# Comprehensive restart functionality for post-conflict scenarios

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "🔄 Atlas Restart Manager"
    echo "========================"
    echo -e "${NC}"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local timeout=${2:-30}
    local count=0
    
    while [ $count -lt $timeout ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    return 1
}

# Function to kill Atlas processes
kill_atlas_processes() {
    print_status "Зупинка існуючих Atlas процесів..."
    
    # Kill by PID file if exists
    if [ -f "data/atlas.pid" ]; then
        local pid=$(cat data/atlas.pid)
        if ps -p $pid > /dev/null 2>&1; then
            print_status "Зупинка Atlas (PID: $pid)..."
            kill $pid
            sleep 2
            if ps -p $pid > /dev/null 2>&1; then
                print_warning "Примусове завершення процесу..."
                kill -9 $pid
            fi
        fi
        rm -f data/atlas.pid
    fi
    
    # Kill any remaining Python Atlas processes
    pkill -f "atlas_core.py" 2>/dev/null || true
    pkill -f "mcp_automation_server.py" 2>/dev/null || true
    pkill -f "mcp_macos_automator.py" 2>/dev/null || true
    
    # Free up ports if they're stuck
    if port_in_use 8000; then
        print_warning "Порт 8000 все ще зайнятий, звільняю..."
        fuser -k 8000/tcp 2>/dev/null || true
    fi
}

# Function to restart Docker services
restart_docker() {
    print_status "Перезапуск Atlas через Docker..."
    
    # Stop existing containers
    if docker compose ps | grep -q "atlas"; then
        print_status "Зупинка існуючих Docker контейнерів..."
        docker compose down
    fi
    
    # Start services
    print_status "Запуск Atlas Docker stack..."
    docker compose --profile monitoring --profile mcp --profile macos up -d
    
    # Wait for services
    print_status "Очікування готовності сервісів..."
    sleep 10
    
    # Check health
    if wait_for_service "http://localhost:8000/status" 60; then
        print_success "Atlas Core запущено успішно"
    else
        print_warning "Atlas Core не відповідає"
    fi
    
    if wait_for_service "http://localhost:8080/health" 30; then
        print_success "3D Frontend запущено успішно"
    else
        print_warning "3D Frontend не відповідає"
    fi
}

# Function to restart local services
restart_local() {
    print_status "Перезапуск Atlas в локальному режимі..."
    
    # Kill existing processes
    kill_atlas_processes
    
    # Start Atlas
    print_status "Запуск Atlas..."
    ./start_atlas.sh --local --background
    
    # Wait and check
    sleep 5
    if wait_for_service "http://localhost:8000/status" 30; then
        print_success "Atlas запущено успішно в локальному режимі"
    else
        print_error "Не вдалося запустити Atlas в локальному режимі"
        return 1
    fi
}

# Function to restart Kubernetes services
restart_kubernetes() {
    local env=${1:-development}
    print_status "Перезапуск Atlas в Kubernetes ($env)..."
    
    if ! command_exists kubectl; then
        print_error "kubectl не знайдено. Встановіть kubectl для роботи з Kubernetes."
        return 1
    fi
    
    # Check if we can connect to cluster
    if ! kubectl cluster-info >/dev/null 2>&1; then
        print_error "Не можу підключитися до Kubernetes кластера."
        return 1
    fi
    
    # Restart deployments
    if [ "$env" = "development" ]; then
        make restart-dev
    elif [ "$env" = "production" ]; then
        make restart-prod
    else
        print_error "Невідоме середовище: $env"
        return 1
    fi
    
    print_success "Kubernetes перезапуск ініційовано для $env"
}

# Function to detect current deployment mode
detect_deployment_mode() {
    # Check for running Docker containers
    if docker compose ps 2>/dev/null | grep -q "atlas"; then
        echo "docker"
        return
    fi
    
    # Check for Kubernetes
    if command_exists kubectl && kubectl get namespace atlas-mcp-dev >/dev/null 2>&1; then
        echo "kubernetes"
        return
    fi
    
    # Check for local processes
    if [ -f "data/atlas.pid" ] || pgrep -f "atlas_core.py" >/dev/null; then
        echo "local"
        return
    fi
    
    # Default to auto-detect
    echo "auto"
}

# Function to show usage
show_usage() {
    echo "Використання: $0 [MODE] [OPTIONS]"
    echo ""
    echo "Режими:"
    echo "  docker      Перезапустити Docker Compose стек"
    echo "  local       Перезапустити локальну Python версію"
    echo "  k8s-dev     Перезапустити Kubernetes development"
    echo "  k8s-prod    Перезапустити Kubernetes production"
    echo "  auto        Автоматично визначити режим (по замовчуванню)"
    echo ""
    echo "Опції:"
    echo "  --force     Примусово завершити всі процеси"
    echo "  --help      Показати цю допомогу"
    echo ""
    echo "Приклади:"
    echo "  $0                    # Автоматичне визначення"
    echo "  $0 docker             # Перезапуск Docker"
    echo "  $0 local              # Перезапуск локально"
    echo "  $0 k8s-dev            # Перезапуск Kubernetes dev"
}

# Main function
main() {
    print_header
    
    local mode="auto"
    local force=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            docker|local|k8s-dev|k8s-prod|auto)
                mode="$1"
                shift
                ;;
            --force)
                force=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Невідомий параметр: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Auto-detect mode if needed
    if [ "$mode" = "auto" ]; then
        detected_mode=$(detect_deployment_mode)
        print_status "Автоматично визначено режим: $detected_mode"
        mode="$detected_mode"
    fi
    
    # Execute restart based on mode
    case "$mode" in
        docker)
            restart_docker
            ;;
        local)
            restart_local
            ;;
        k8s-dev)
            restart_kubernetes "development"
            ;;
        k8s-prod)
            restart_kubernetes "production"
            ;;
        auto)
            print_status "Система не запущена, використовую Docker режим..."
            restart_docker
            ;;
        *)
            print_error "Невідомий режим: $mode"
            exit 1
            ;;
    esac
    
    echo ""
    print_success "🎉 Перезапуск Atlas завершено!"
    echo ""
    print_status "📋 Перевірте статус:"
    echo "   • Web Interface: http://localhost:8000"
    echo "   • API Docs: http://localhost:8000/docs"
    echo "   • Status: http://localhost:8000/status"
    if [ "$mode" = "docker" ]; then
        echo "   • 3D Frontend: http://localhost:8080"
    fi
    echo ""
}

# Run main function
main "$@"